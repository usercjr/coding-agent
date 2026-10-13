from agent.tools.base import Tool, register
name = "dispatch_parallel"

description = (
    "把【多个】相互独立的子任务【并行】派给多个子 agent 同时完成，返回所有结果。"
    "当有几个彼此不依赖、可同时进行的子任务时使用(如同时调研多个模块)。"
    "参数 tasks 是子任务描述的列表,每个描述都要自包含。"
)

parameters = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",                    # ← 新:数组类型
            "items": {"type": "string"},        # ← 数组里每个元素是字符串
            "description": "多个子任务描述的列表",
        },
    },
    "required": ["tasks"],
}

def dispatch_parallel(tasks):
    from agent.loop import run_parallel   # 延迟 import 破循环(和 dispatch 一样)
    return run_parallel(tasks)

register(Tool(name=name, description=description, parameters=parameters, execute=dispatch_parallel))
