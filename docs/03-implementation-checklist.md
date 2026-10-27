# 实施清单（MVP：S7 + S1 + S2 + S4）

> 用法：对着做，每完成一步勾一个框。
> **代码自己写**；卡住了就按「提示阶梯」一层一层问，不要一上来就要答案。
>
> 提示阶梯：`给方向` → 自己再试 → `给伪代码/签名` → 自己再试 → `给真实代码`
> （两次为限，见 `CLAUDE.md`）

---

## Step 0 · `/ask` 随问随答（S7）—— 先做这个

> 工作量最小、每天都用得上，而且 `pydoc_lookup` 这个工具后面 S2/S3 都会复用。

### 0.1 `pydoc_lookup` 工具

- [ ] 新建 `agent/tools/pydoc_lookup.py`，四件套照抄 `agent/tools/grep.py` 的结构
- [ ] 在 `agent/tools/__init__.py` 和 `agent/loop.py::ALLOWED_TOOLS` 里各加一处注册
- [ ] 实现 `_resolve(target)`：把 `"contextvars.ContextVar"` 解析成真正的对象
      —— **必须用 `importlib` + `getattr` 逐段取，严禁 `eval`/`exec`**
- [ ] 实现 `pydoc_lookup(target)`：返回真实签名（`inspect.signature`）+ docstring（`inspect.getdoc`）
- [ ] 查不到时返回明确的「查不到 + 原因」，**不要返回空串**（空串会让模型开始编）

**验收**：
```
pydoc_lookup("contextvars.ContextVar")  → 能看到真实的类签名和官方 docstring
pydoc_lookup("dict.setdefault")         → 能看到 setdefault 的 docstring
pydoc_lookup("不存在的东西")             → 明确告诉你查不到，而不是空白
pydoc_lookup("os.path.join")            → 能正确穿过「模块.模块.函数」三段
```

**坑提醒**：
- `inspect.signature` 对 C 实现的内置函数（如 `dict.setdefault`）可能抛 `ValueError`
  —— 要兜住，docstring 还是能拿到的
- `**args` 解包、列表推导式这类**语法糖**根本不是对象，`_resolve` 查不到是正常的
  → 这种情况应该优雅降级，让模型用自己的知识回答，并**标注「以下来自模型知识，非本地查证」**

### 0.2 `/ask` 入口 + 回答规范

- [ ] 新建 `skills/asking/SKILL.md`：写死 L1 一句话 → L2 解决什么问题 →
      L3 本项目真实用例（带 `文件:行号`）→ L4 常见坑，并明确 **一次给完，不要反问**
- [ ] skill 里要求：先调 `pydoc_lookup` 拿事实，再调 `grep` 搜本项目用例
- [ ] 在 `main.py` 的 `COMMANDS` 里加 `"ask"`，并在 `/help` 补上
- [ ] **解决「教学模式反问」冲突**（见 `docs/02` S7 动手前想清楚第 1 题）

**验收**（这条最关键）：
1. 开着 `/teach`，执行 `/ask contextvars.ContextVar`
2. agent 必须**直接给答案，不能反问「你觉得呢」**
3. 回答里必须出现 `agent/workdir.py` 这个**本项目的真实用例**
4. 再执行一次普通的概念提问（比如「为什么子 agent 要独立 messages」），
   agent 应该**恢复反问引导** —— 证明 `/ask` 的例外是**局部的**，没有把教学模式整个关掉

> 第 4 条是真正的难点。如果你的实现把教学模式**永久**关掉了，那就是 bug。

### 自检题（做完回答）
1. 你用哪种方式让 `/ask` 压过了 teaching skill 的反问规则？
   另外两种方式分别会在什么情况下失效？
2. 为什么 `_resolve` 不能用 `eval(target)`？把这件事和 `agent/default_hooks.py`
   的 5 层限权联系起来说一说。
3. `pydoc_lookup` 查不到时，为什么**返回「查不到」比返回空串重要**？
   （提示：想想模型拿到空串会干什么）

---

## Step 1 · `codemap` 工具（S1）

### 1.1 骨架层：模块 + 顶层定义

- [ ] 新建 `agent/tools/codemap.py`，照着 `agent/tools/grep.py` 的样子写工具四件套
- [ ] 在 `agent/tools/__init__.py` 的 import 列表里加上 `codemap`
- [ ] 在 `agent/loop.py` 的 `ALLOWED_TOOLS` 里加上 `"codemap"`
- [ ] 实现 `_scan_file`：用 `ast` 解析单文件，拿到顶层函数/类名、行号、参数名、docstring 首句
- [ ] 实现 `codemap(path, depth="outline")`：遍历目录下的 `.py`，拼成紧凑文本

**验收**：在项目根目录跑 `codemap(".")`，输出里应该能看到 `agent/loop.py` 的
`_agent_loop` / `run` / `run_subagent` / `run_parallel`，且**总输出不超过 ~80 行**。

**坑提醒**：
- 别忘了跳过 `.venv/`、`__pycache__/`、`.worktrees/`（否则输出会爆炸）
- 文件语法错误时 `ast.parse` 会抛异常 —— 工具不能因为一个坏文件就整个崩

### 1.2 调用边层

- [ ] `depth="calls"` 时额外输出 import 边和函数调用边
- [ ] **显式输出「盲区」清单**：动态分发（`tool.execute(**args)`）、`getattr` 调用等

**验收**：对 `agent/loop.py` 跑一次，输出里必须出现
「`tool.execute(**args)` 是动态分发，静态分析无法确定实际调用的工具」这类提示。
—— 这条是刻意设计的，一个**诚实报告自己盲区**的工具，才配用来教人。

### 1.3 阅读顺序层

- [ ] `depth="order"` 时输出建议阅读顺序
- [ ] 处理循环依赖（不能死循环）

**自检题（做完回答）**：
1. 为什么 `codemap` 必须是 Tool 而不能是 Skill？用「事实归工具，叙述归模型」解释。
2. 你的阅读顺序算法在遇到 A↔B 循环依赖时是怎么兜住的？代价是什么？

---

## Step 2 · `/explain` 分层讲解（S2）

- [ ] 新建 `skills/explaining/SKILL.md`（frontmatter 的 `name` / `description` 格式照抄 `teaching`）
      —— 写死 L1 一句话 → L2 结构 → L3 关键决策 → L4 逐行，并强调**一次只讲一层，讲完必须停下来问**
- [ ] 在 `main.py` 的 `COMMANDS` 里加 `"explain"`，模板要求先 `load_skill("explaining")` 再调 `codemap`
- [ ] 在 `/help` 的输出里补上这条

**验收**：开 `/teach`，执行 `/explain agent/default_hooks.py`，
agent 应该**只讲 L1 就停住**问你要不要继续，而不是一口气讲到逐行。

**自检题**：
1. `COMMANDS` 现在是 `dict[str, str]`（纯模板）。`/explain` 用纯模板够用吗？
   如果不够，你打算怎么改这个结构？改了之后 `handle_slash` 要跟着动哪几行？（这是涟漪效应练习）
2. 为什么 L3「为什么这么写」要排在 L4「逐行」前面？

---

## Step 3 · `/breakit` 破坏式学习（S4）

- [ ] 读懂 `agent/loop.py::_run_in_worktree`，搞清楚 `set_cwd` 是怎么把文件操作路由进 worktree 的
- [ ] 设计「破坏类型清单」（删边界检查 / 改比较符 / 去掉 try / 调换参数顺序 ...）
- [ ] 新建 `skills/breaking/SKILL.md` 或直接做成 Slash —— **先自己判断该放哪一层**，再动手
- [ ] 流程：建 worktree → 改坏一处 → 告诉用户「坏在 X 文件，去找」→ 用户猜 → 揭晓 + `git diff`
- [ ] **补上 worktree 清理**（`git worktree remove`），顺手还掉现有的那笔小债

**验收**：对 `agent/loop.py::maybe_compress` 跑一次，
它应该能删掉「recent 不能以孤儿 tool 消息开头」那个 while 循环，
而你能说出后果：*压缩后第一条是 tool 消息，没有配对的 tool_calls，API 会报错*。

**自检题**：
1. 为什么用 worktree 而不是直接复制到 `/tmp`？用 git 的角度回答。
2. 如果用户工作区有**未提交**的改动，`git worktree add` 出来的副本里有没有这些改动？
   这对 `/breakit` 意味着什么？

---

## 不属于 MVP，但做完上面可以接着做

- [ ] S3 `/quiz` + `agent/learning_state.py`（记得把状态文件加进 `.gitignore`）
- [ ] S5 `/due` 间隔复习
- [ ] S6 教学质量评测（`kind="teach"` + 模拟学生 + 多轮 runner）

---

## 每完成一个 Step 要做的事

1. 在 `docs/DEVLOG.md` 追加一条（动机 / 改了哪些文件 / 留了什么坑）
2. 回到 `docs/02-design-learning-features.md`，把对应方案标成 `[已实现]`
3. 回答上面的自检题 —— **答不上来的，说明那块还没真懂，别往下走**
