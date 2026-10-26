# Coding Agent

从零用 Python 实现的命令行自主编码代理（同类:Claude Code / DeepSeek Harness 的精简版）。
具备自主工具调用、多 Agent 并行、纵深安全与可量化评测;并内置可开关的**教学模式**,可将代理从"代写工具"切换为"陪练导师"。

> 后端模型通过 OpenAI 兼容 API 调用（默认 DeepSeek），换模型只需改适配层。

## ✨ 核心特性

- **自主 Agent 引擎**:ReAct 循环（思考 → 调工具 → 观察 → 自纠），工具以统一**注册表**管理、数据驱动分发;非法 JSON / 未知工具 / 工具异常均兜底不崩。
- **6 大内置工具**:`read_file` / `write_file` / `edit_file`（精确唯一匹配替换）/ `bash`（超时+输出截断）/ `glob` / `grep`。
- **MCP 协议**:内置 MCP Client，运行时动态挂载外部 MCP Server 的工具，与内置工具同表、统一分发。
- **Skill + Slash + Hook**:
  - Skill 渐进式加载（简介常驻、正文按需 `load_skill`）。
  - Slash Command（`/help` `/review` `/auto` `/teach`）。
  - 生命周期 Hook（事件总线 / 观察者模式，`pre_tool` / `post_tool`）。
- **纵深安全（5 层限权）**:工具白名单 / 路径沙箱（`realpath` 防穿越）/ 命令校验 / 人工确认 / 审计日志;执行层只校验实际操作,可防 Prompt Injection。
- **上下文与记忆**:超阈值 LLM 摘要压缩（保留 system + 最近 N 轮，处理 tool_call 配对边界）;跨轮次 + 跨会话持久化记忆。
- **多 Agent 并行**:SubAgent 上下文隔离分发（`dispatch`）+ **Git Worktree 并行**（`dispatch_parallel`，多子代理在独立工作副本同时改代码不冲突）;用 `contextvars` 实现每线程工作目录隔离。
- **教学内核（差异化）**:`/teach` 开关注入教学 playbook,代理按"分级提示 → Socratic 提问 → 出题检验"引导用户自己实现,而非直接代写。
- **评测闭环**:自建评测集 + 执行验证（对标 SWE-bench 思路）+ LLM-as-Judge（开放式任务）,每题在隔离临时环境中运行,自动统计任务成功率。

## 📁 结构

```
agent/
  loop.py          # Agent Loop 内核（_agent_loop）+ 主/子 agent + 并行 + 压缩 + 教学开关
  workdir.py       # 每线程工作目录（contextvars），并行隔离的地基
  hooks.py         # 事件总线（register_hook / fire）
  default_hooks.py # 5 层安全钩子 + 确认开关 + 审计
  mcp_client.py    # MCP 客户端（stdio）
  tools/           # 工具：6 大内置 + load_skill / remember / dispatch / dispatch_parallel
skills/            # Skill 技能包（teaching 教学内核 / code-review）
eval/              # 评测闭环：cases.py（评测集）+ run_eval.py（harness）
main.py            # CLI 入口（REPL + Slash Command）
```

## 🚀 运行

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=your-key        # Windows: set DEEPSEEK_API_KEY=your-key
python main.py
```

常用命令:`/help` 查看命令,`/teach` 开/关教学模式,`/auto` 开/关自动批准,`exit` 退出。

## 📊 跑评测

```bash
python -m eval.run_eval
```

对评测集逐题运行代理（隔离临时环境）→ 执行验证 / LLM-as-Judge 判定 → 打印任务成功率。

## 📚 开发文档

设计决策与开发过程都记录在 [`docs/`](docs/) 里，换台电脑 clone 下来也能看到「当时为什么这么改」：

- [`docs/00-INDEX.md`](docs/00-INDEX.md) — 文档索引
- [`docs/DEVLOG.md`](docs/DEVLOG.md) — 变更日志（每次开发动了哪些文件、留了什么坑）
- [`docs/01-gap-analysis.md`](docs/01-gap-analysis.md) — 现状盘点与应用性缺口
- [`docs/02-design-learning-features.md`](docs/02-design-learning-features.md) — 代码学习能力设计方案与 trade-off
- [`docs/03-implementation-checklist.md`](docs/03-implementation-checklist.md) — 分步实施清单与自检题

## 🛠 技术栈

Python · OpenAI 兼容 API（DeepSeek）· MCP · Git Worktree · threading / contextvars · subprocess · ReAct · LLM-as-Judge
