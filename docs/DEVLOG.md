# 开发日志（DEVLOG）

> 倒序排列，最新的在最上面。
> 每条必须写清：**动机 / 改了哪些文件 / 留了什么坑**。
> AI 协作的 session 也要在这里留痕，方便换台电脑后知道「上次发生了什么」。

---

## 2026-10-27 · 增补 S7：`/ask` 随问随答（Python 基础 / 陌生 API 即时查词）

**动机**
看代码时卡住人的往往不是架构，而是**一个不认识的 API**（`contextvars.ContextVar`、
`dict.setdefault`、`ast.walk`……）。现在只能切出去查文档，注意力被打断，
而且开着 `/teach` 时还会被苏格拉底式反问 —— 查字典被反问「你猜猜看」是纯折磨。

**改了哪些文件（仍为纯文档，未动实现代码）**

| 文件 | 操作 | 说明 |
| --- | --- | --- |
| `docs/01-gap-analysis.md` | 修改 | 新增「缺口 4：看代码时的即时查词没人管」+ 映射表一行 |
| `docs/02-design-learning-features.md` | 修改 | 新增 S7 完整方案；总表加一行；落地顺序改为 S7 打头 |
| `docs/03-implementation-checklist.md` | 修改 | 新增 Step 0（S7），MVP 调整为 S7 + S1 + S2 + S4 |
| `docs/DEVLOG.md` | 修改 | 本条 |

**本次得出的核心结论**
1. **不是所有问题都该被「教」。** 要区分两类：
   - *概念理解*（「为什么子 agent 要独立 messages」）→ 引导、反问；
   - *事实查询*（「`setdefault` 是干嘛的」）→ **直接答，不许反问**。
   所以 `/ask` 必须能**局部压过** teaching skill 的反问规则，且**不能把教学模式整个关掉**。
   这条对应 `CLAUDE.md` 的「别抠太细，必要时直接给答案」。
2. 事实来源优先级：**① 本地 introspection（`importlib`+`inspect`，100% 准确）
   → ② 项目内真实用例（复用 `grep`）→ ③ 模型知识（标注「未经本地查证」）**。
   又一次印证「事实归工具，叙述归模型」。
3. ② 是相对「直接问通用聊天机器人」的最大差异化：拿**用户自己写过的代码**当例子。
4. 落地顺序调整：**S7 排到最前面** —— 工作量最小、频率最高，且它产出的
   `pydoc_lookup` 后面 S2 `/explain`、S3 `/quiz` 都会复用。

**留下的坑 / 待办**
- [ ] `_resolve` 严禁 `eval`/`exec`（现成的 RCE）；必须 `importlib` + `getattr` 逐段取。
- [ ] import 陌生模块会执行其顶层代码 —— 要不要限制只查标准库 + 已安装第三方库？待定。
- [ ] 「`/ask` 的例外必须是局部的」缺少自动化验证手段，目前只能靠 Step 0 的人工验收第 4 条；
      等 S6 教学评测做出来后应该补一条用例。
- [ ] 上一条 DEVLOG 里的三个坑仍未还（worktree 不清理 / `COMMANDS` 结构 / `run_one` 单轮）。

**推送状态**：`git push` 与 GitHub API 写入均被 403 拒绝（Claude 对本仓库无写权限），
本次与上次的提交都只在本地分支 `claude/code-learning-applicability-docs-c9plvh` 上。

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
