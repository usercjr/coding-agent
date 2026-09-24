"""跨会话记忆：remember 工具（写）+ load_memory 辅助函数（读）。

- remember：模型判断“该长期记住”时调用，把一条事实追加进 memory.md。
- load_memory：启动时读 memory.md，注入 system prompt（读的套路同 available_skills_text）。
"""

from agent.tools.base import Tool, register

MEMORY_FILE = "memory.md"

name = "remember"

description = (
    "把一条值得长期记住的事实写入记忆(跨会话保留)。"
    "当用户确立了项目约定、重要决策、方案,或希望你记住某事时使用。"
    "只记长期有用的,不要记临时命令输出。参数 fact 是要记住的一句话。"
)

parameters = {
    "type": "object",
    "properties": {
        "fact": {"type": "string", "description": "要长期记住的一条事实"},
    },
    "required": ["fact"],
}


def remember(fact):
    try:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:   # "a" 追加，记忆累积不覆盖
            f.write(f"- {fact}\n")
        return f"已记住:{fact}"
    except OSError as e:
        return f"记忆写入失败:{e}"


def load_memory():
    """启动时读 memory.md 全文；还没有文件就返回空串（不崩）。"""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


register(Tool(name=name, description=description, parameters=parameters, execute=remember))
