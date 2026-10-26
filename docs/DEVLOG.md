# 开发日志（DEVLOG）

> 倒序排列，最新的在最上面。
> 每条必须写清：**动机 / 改了哪些文件 / 留了什么坑**。
> AI 协作的 session 也要在这里留痕，方便换台电脑后知道「上次发生了什么」。

---

## 2026-10-26 · 新增 docs/ 开发文档体系，产出「代码学习能力」设计方案

**动机**
项目已经把 agent 工程的底座（工具注册表 / ReAct 内核 / Skill / Hook / worktree 并行 / eval）
搭完了，但**「教学」这一块只有一个 prompt skill**，缺少真正能帮人学代码的功能。
同时需要把开发过程沉淀成仓库里的文档，换电脑也能看到改了什么。

**改了哪些文件（本次纯文档，未动任何实现代码）**

| 文件 | 操作 | 说明 |
| --- | --- | --- |
| `docs/00-INDEX.md` | 新增 | 文档索引 + 文档约定 |
| `docs/DEVLOG.md` | 新增 | 本文件 |
| `docs/01-gap-analysis.md` | 新增 | 现有能力盘点 + 三个应用性缺口 |
| `docs/02-design-learning-features.md` | 新增 | S1–S6 设计方案、四大 trade-off、接口草图 |
| `docs/03-implementation-checklist.md` | 新增 | MVP(S1/S2/S4) 分步清单 + 验收标准 + 自检题 |
| `README.md` | 修改 | 增加「开发文档」区块，指向 docs/ |

**本次得出的核心结论**
1. 教学模式现在**只有「嘴」（prompt），没有「手」（工具）和「眼」（掌握度度量）**。
2. 设计原则定为：**事实归工具，叙述归模型**。
3. 最大的杠杆不是加新轮子，而是**把已有的 worktree 隔离 和 LLM-as-Judge 复用到教学场景**
   （S4 复用 `_run_in_worktree`，S3 复用 `eval/run_eval.py::check_judge`）。

**留下的坑 / 待办**
- [ ] `agent/loop.py::_run_in_worktree` 建了 worktree 但**从不清理**，`.worktrees/` 会越堆越多
      —— 实现 S4 时顺手还掉。
- [ ] `main.py` 的 `COMMANDS` 是 `dict[str, str]` 纯模板，扩展到 `/explain`、`/quiz` 时
      可能需要升级结构（典型的涟漪效应练习，见 `docs/03` Step 2 自检题）。
- [ ] `eval/run_eval.py::run_one` 是单轮的，做不了多轮教学评测（S6 的前置障碍）。
- [ ] 设计稿里所有方案都还是 `[未实现]` 状态，实现后要回到 `docs/02` 标注。

---

## 2026 年之前 · 基线（由 git log 回溯整理）

| commit | 内容 |
| --- | --- |
| `00ad1a7` | docs: 添加 README |
| `de79adb` | feat: 多 Agent 并行（Worktree + contextvars）、教学内核（`/teach`）、评测闭环（exec + LLM-judge） |
| `28271eb` | init: 模块 1–7 基线（工具注册表、ReAct 循环、MCP、Skill/Slash/Hook、安全、记忆、压缩） |
