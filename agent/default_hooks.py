"""安全钩子：import 本模块即完成注册。5 层限权中的 ②③④⑤ 大多挂在这里。

- audit_pre  ：⑤ 审计（基础）——每次调工具前打一行日志（只记录，放行）。
- safety_pre ：③ 命令校验——拦截 bash 里的危险命令。
- sandbox_pre：② 路径沙箱——文件操作限制在工作目录内。
- confirm_pre：④ 人工确认——高危工具执行前弹 y/n。
"""

import os
from agent.hooks import register_hook
from datetime import datetime

def audit_pre(context):
    print(f"[hook] 即将调用工具:{context['name']}  参数:{context['args']}")
    return None                      # 只记录，不拦截 → 放行


def safety_pre(context):
    if context["name"] == "bash":
        cmd = context["args"].get("command", "")
        if "rm -rf" in cmd:
            return f"危险命令被拦截:{cmd}"   # 返回原因 = 拦截
    return None                              # 安全 → 放行


WORKDIR = os.path.realpath(".")   # 工作目录的真实绝对路径（启动时算一次）


def sandbox_pre(context):
    args = context["args"]
    if "path" in args:
        target = os.path.realpath(args["path"])
        # WORKDIR + os.sep 是“在工作目录内”的前缀；不是 WORKDIR 本身、也不以该前缀开头 → 目录外 → 拦截, os.sep精确定义"在里面"的边界, 名字像、其实在外面"的目录不被误判成"里面" → 正确拦截。
        if target != WORKDIR and not target.startswith(WORKDIR + os.sep):
            return f"路径越界被拦截:{args['path']}"
    return None    # 没有 path 参数，或路径合法 → 放行


NEEDS_CONFIRM = {"write_file", "edit_file", "bash"}   # 高危工具集合（会改动/执行）

# ---- 确认开关（A：会话级自动批准；D：子 agent 内不确认）----
_auto_approve = False   # A：/auto 切换。True = 本会话不再弹确认
_in_subagent = False    # D：run_subagent 期间为 True，子任务内的操作不弹确认


def set_auto_approve(on):
    global _auto_approve          # 要改模块级变量，必须声明 global
    _auto_approve = on


def is_auto_approve():
    return _auto_approve


def set_in_subagent(on):
    global _in_subagent
    _in_subagent = on


def confirm_pre(context):
    if _auto_approve or _in_subagent:    # A 或 D 命中 → 跳过确认，直接放行
        return None
    if context["name"] in NEEDS_CONFIRM:
        ans = input(f"⚠️  确认执行 {context['name']} {context['args']}? [y/N] ")
        if ans.strip().lower() == "y":
            return None                  # 用户确认 → 放行
        return "用户取消了操作"           # 其它输入 → 拦截
    return None    # 非高危工具，直接放行

# 把审计日志写入文件带结果，
def audit_post(context):
    # 往 audit.log 追加一行:时间 + 工具名 + 参数 + 结果(截断,别太长)
    with open("audit.log", "a", encoding="utf-8") as f:
        line = f"{datetime.now()} {context['name']} {context['args']} -> {str(context['result'])[:200]}\n"
        f.write(line)
    return None

# 注册顺序有讲究：便宜的自动判断在前，打扰用户的确认在最后（被前面拦掉就不必弹确认）
register_hook("pre_tool", audit_pre)
register_hook("pre_tool", safety_pre)
register_hook("pre_tool", sandbox_pre)
register_hook("pre_tool", confirm_pre)
register_hook("post_tool", audit_post)