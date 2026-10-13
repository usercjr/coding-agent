import os
import json
from openai import OpenAI
import agent.tools               # ← 触发所有工具注册
from agent.tools import base
from agent.tools.load_skill import available_skills_text, load_skill   # 扫描简介 / 读 skill 正文
from agent.tools.remember import load_memory               # 读 memory.md 跨会话记忆
from agent import hooks
from agent.default_hooks import set_in_subagent    # D：子 agent 内不确认
from concurrent.futures import ThreadPoolExecutor
import subprocess
from agent.workdir import set_cwd
import time  


# agent 调用主流程，main 调用 run()

api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY")
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

# loop.py 顶部定义白名单:只留这些工具
ALLOWED_TOOLS = {
    "read_file", "write_file", "edit_file", "bash", "glob", "grep", "load_skill",
    "remember",            # 跨会话记忆工具
    "dispatch",            # 派1个子任务给子 agent，同步把他跑完
    "dispatch_parallel",   # 派一批子任务给多个agent，多线程同时跑，调 run_subagent(task)	
    "echo", "get-sum",     # 从 13 个 MCP 工具里只留这两个有用的，调 run_parallel(tasks)→内部对每个 task 并发调 run_subagent
}

# 子 agent 可用工具：不含 dispatch(防无限套娃)、不含 remember(子 agent 不写长期记忆)
SUBAGENT_TOOLS = {
    "read_file", "write_file", "edit_file", "bash", "glob", "grep", "load_skill",
}

# 模块级持久对话：整个会话（python main.py 期间）共享同一个 messages，
# system 只放一次；每次 run 往里追加用户输入，历史累积 → agent 记得住前面聊的
system_prompt = (
    "你是一个编码助手。\n"
    "以下是你跨会话记住的事实（记忆），请在相关时参考:\n"
    + load_memory() + "\n"
    "以下是可用技能，当任务匹配某个技能时，先用 load_skill 工具加载它的完整说明再执行:\n"
    + available_skills_text() + "\n"
    "当用户确立了项目约定/重要决策/方案，或明确要你记住某事时，用 remember 工具存入记忆。"
)
messages = [{"role": "system", "content": system_prompt}]


# ---------- 教学模式开关（模块 8：/teach 切换，开启时把教学 playbook 注入 system）----------
_teach = False


def set_teach(on):
    global _teach
    _teach = on
    # 开 → 原 system_prompt + 教学 playbook 正文；关 → 恢复原 system_prompt
    messages[0]["content"] = system_prompt + ("\n\n" + load_skill("teaching") if on else "")


def is_teach():
    return _teach

# ---------- 上下文压缩 ----------
MAX_CONTEXT_CHARS = 8000   # 超过这个长度就压缩（学习用字符数粗估，非真实 token）
KEEP_RECENT = 6            # 保留最近多少条原文


def _role_of(m):
    """判断是不是字典，统一取得到 role来判断压缩后不能是tool开头：dict 用 ["role"]取得内容，OpenAI 消息对象用 .role。"""
    return m["role"] if isinstance(m, dict) else m.role


def _total_chars(msgs):
    """所有消息文本长度之和，作为“该不该压”的信号。"""
    return sum(len(str(m)) for m in msgs)


def _summarize(old_msgs):
    """把早期消息交给 LLM 生成摘要。"""
    text = "\n".join(str(m) for m in old_msgs)
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "把下面的对话历史压成简洁摘要，保留关键事实、决定、已完成的操作和读到的重要内容，去掉冗余过程。"},
            {"role": "user", "content": text},
        ],
    )
    return resp.choices[0].message.content


def maybe_compress():
    """token（这里用字符数）超阈值时：把中间老对话压成摘要，保留 system + 最近 N 条。"""
    if _total_chars(messages) < MAX_CONTEXT_CHARS:
        return
    system = messages[0]
    recent = messages[-KEEP_RECENT:]
    # 边界保护：recent 不能以“孤儿 tool 消息”开头（它配对的 tool_calls 会被压走）
    while recent and _role_of(recent[0]) == "tool":
        recent = recent[1:]
    middle = messages[1:len(messages) - len(recent)]   # system 和 recent 之间的老对话
    if not middle:
        return
    summary = _summarize(middle)
    # 原地替换（messages[:] 而不是 messages=... ，保持模块级引用不变）
    messages[:] = [system, {"role": "user", "content": "[前情摘要]\n" + summary}, *recent]
    print(f"[压缩] 历史已摘要，保留最近 {len(recent)} 条原文")

def _agent_loop(msgs, allowed, compress=False):
    """通用循环内核:调 API → 分发工具 → 直到最终答复，return 最终文本。"""
    for _ in range(20):
        if compress:
            maybe_compress()          # 只有主 agent 传 compress=True 才压
        # 👇 把 run 里 for 循环体的内容搬到这里，做 4 处替换（见下）
        # 1. 调 API
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=msgs,
            tools=base.all_openai_schemas(allowed),
        )
        msg = resp.choices[0].message   # 模型这次说的话（含 content 和 tool_calls）

        # 2. 把模型这条回复塞回历史（记住它说了啥）
        msgs.append(msg)

        # 3. 没有要调工具 → 模型给了最终答复
        if not msg.tool_calls:
            return msg.content

        # 4. 有 tool_calls → 逐个分发执行，把结果塞回历史，每一次的tool_call都要确保返回历史
        for call in msg.tool_calls:
            name = call.function.name

            # 参数解析：模型偶尔给出非法 JSON，兜底（仍要回一条结果，满足“每个 tool_call 都有回应”）
            try:
                args = json.loads(call.function.arguments)
            except json.JSONDecodeError as e:
                msgs.append({"role": "tool", "tool_call_id": call.id,
                                 "content": f"错误:参数不是合法 JSON - {e}"})
                continue

            # 分发：工具名不存在时不崩，回一条错误结果
            tool = base.get(name)
            if tool is None:
                result = f"错误:找不到名为 {name} 的工具"
            else:
                # pre_tool:执行前广播。被拦截(返回原因)就不执行
                reason = hooks.fire("pre_tool", {"name": name, "args": args})
                if reason:
                    result = f"操作被拦截:{reason}"
                else:
                    # 执行本身也可能抛异常（缺参、工具内部出错），兜住不崩，回错误给模型自纠
                    try:
                        result = tool.execute(**args)
                    except Exception as e:
                        result = f"错误:工具 {name} 执行失败 - {e}"

                    # context里面放的是即将执行的工具和内容args
                    hooks.fire("post_tool", {"name": name, "args": args, "result": result})
            msgs.append({"role": "tool", "tool_call_id": call.id, "content": result})        
            # for 结束后，回到第 1 步（带着工具结果再问模型）
    return "已达到最大轮数上限,任务未完成。"    # for 跑完没结束 → return（不再 print）

def run(user_input):
    messages.append({"role": "user", "content": user_input})
    result = _agent_loop(messages, ALLOWED_TOOLS, compress=True)   # 主:传全局 messages + 全工具 + 开压缩
    print(result)                                                  # 主:负责打印

def run_subagent(task):
    # 1. 新建一个【局部】messages（隔离！不用全局那个）
    #    - 一条 system:告诉子 agent 它的角色(独立完成任务、给简洁结论)
    #    - 一条 user:内容就是 task
    sub_messages = [
        {"role": "system", "content": "你是一个子任务执行 agent，独立完成下面的任务，最后给出简洁的结论/结果。"},
        {"role": "user", "content": task}, # 这是部分用户输入，主agent切分后把任务喂给子agent,这是最关键的漏项
    ]
    # 2. 调 _agent_loop：子 agent 期间关掉确认（D）。try/finally 保证出错也复位
    set_in_subagent(True)
    try:
        result = _agent_loop(sub_messages, SUBAGENT_TOOLS, compress=False)
    finally:
        set_in_subagent(False)
    # 3. return 它的结果（不 print——结果要交回主 agent，不是给用户看）
    return result

def run_parallel(tasks):
    # tasks 是一串子任务描述(list of str)
    # 用 ThreadPoolExecutor 并发跑 run_subagent,收集所有结果
    # 返回结果列表(可以拼成一段文本,标明第几个任务的结果)

    n = min(len(tasks),5) # 可以最多执行多少个tasks
    with ThreadPoolExecutor(max_workers=n) as pool:
        # pool.map(fn, 列表1, 列表2) → 并发调 fn(列表1[i], 列表2[i])
        results = list(pool.map(_run_in_worktree, range(len(tasks)), tasks))
        # 拼成"任务i结果:..."的形式,便于主 agent/用户看清哪个是哪个
    return "\n\n".join(f"【任务{i+1}】{r}" for i, r in enumerate(results))

def _run_in_worktree(i, task):
    branch = f"task-{int(time.time())}-{i}"
    wt = f".worktrees/{branch}"
    # 1. 建 worktree(新分支 branch,目录 wt)——git 命令:
    r = subprocess.run(["git","worktree","add","-b",branch,wt], capture_output=True, text=True)
    if r.returncode != 0:
        return f"建 worktree 失败:{r.stderr}"   # 不继续 set_cwd/跑子agent
    
    # 2. 把本线程的工作目录设成这个 worktree(用它的真实绝对路径)
    set_cwd(os.path.realpath(wt))
    # 3. 跑子 agent
    result = run_subagent(task)
    # 4. return 结果 + 标明改动在哪(便于人审)
    return f"{result}\n(改动在分支 {branch} / 目录 {wt})"




