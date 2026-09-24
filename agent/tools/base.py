"""工具抽象 + 注册表。

模块 1 的核心：所有工具共用一套结构（四件套），并集中登记到一张注册表里，
供 Agent Loop 统一分发（dispatch）。这样加工具不用改分发逻辑，也为 MCP
运行时动态挂载外部工具打好底子。
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    """一个工具 = 四件套。

    name / description / parameters 三项是「给模型看的」，会打包成 schema
    发给 LLM；execute 是「本地执行代码」，模型永远拿不到，只有分发时本地调用。
    """

    name: str            # 工具名，也是注册表的 key，模型靠它指定调哪个工具
    description: str     # 给模型看的说明：这工具干什么、何时用、返回什么
    parameters: dict     # 参数的 JSON Schema，对应 Anthropic API 的 input_schema
    execute: Callable    # 本地函数：execute(**参数) -> 结果（模型碰不到）

    def to_schema(self) -> dict:
        """转成 Anthropic 格式的 schema：只含前三件，不含 execute。"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai_schema(self) -> dict:
        """转成 OpenAI / DeepSeek 格式的 schema（外套一层 function，key 用 parameters）。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# 这是注册表：name -> Tool 的映射。
# 把「工具名」和「工具实现」解耦成数据，分发逻辑对工具数量/种类零感知；
# 加工具 = 往 dict 里塞一项，MCP 也能在运行时把远端工具挂进来。
_REGISTRY: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    """登记一个工具。同名重复直接报错（fail loud），避免悄悄覆盖藏 bug。"""
    if tool.name in _REGISTRY:
        raise ValueError(f"工具 {tool.name} 已注册")
    _REGISTRY[tool.name] = tool


def get(name: str) -> Tool | None:
    """按名查工具，查不到返回 None（交给分发处决定怎么回给模型）。"""
    return _REGISTRY.get(name)


def all_schemas() -> list[dict]:
    """收集所有工具的 Anthropic 格式 schema。"""
    return [tool.to_schema() for tool in _REGISTRY.values()]


def all_openai_schemas(allowed=None) -> list[dict]:
    """收集工具的 OpenAI / DeepSeek 格式 schema。

    allowed 为 None → 返回全部；给一个工具名集合 → 只返回其中的（① 工具白名单）。
    """
    schemas = [tool.to_openai_schema() for tool in _REGISTRY.values()]
    if allowed is not None:
        schemas = [s for s in schemas if s["function"]["name"] in allowed]
    return schemas
