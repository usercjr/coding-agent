"""dispatch 工具：把独立子任务派给子 agent。

主 agent 调 dispatch → 子 agent 用独立上下文跑完 → 只把最终结果返回主 agent，
中间过程不污染主对话。
"""

from agent.tools.base import Tool, register

name = "dispatch"

description = (
    "把一个独立、可自成一体的子任务派给子 agent 完成，只返回它的最终结果。"
    "适合'可隔离、步骤多、中间过程你不必看到'的子任务(如调研某模块、批量处理)。"
    "参数 task 是对子任务的完整描述(子 agent 看不到当前对话，需交代清楚)。"
)

parameters = {
    "type": "object",
    "properties": {
        "task": {"type": "string", "description": "子任务的完整描述"},
    },
    "required": ["task"],
}


def dispatch(task):
    # 延迟 import：loop 顶部 import 了 agent.tools（含本文件），
    # 若这里在顶部 import loop 会循环导入 → 放进函数里、用到才导。
    from agent.loop import run_subagent
    return run_subagent(task)


register(Tool(name=name, description=description, parameters=parameters, execute=dispatch))
