import glob as globlib   # 模块也叫 glob,和工具函数重名 → 必须起别名
from agent.tools.base import Tool, register
# globlib.glob(pattern, recursive=True) 返回匹配的路径 list
# recursive=True 才能让 ** 生效(递归进子目录)

# 它是 agent 的"找文件"工具。给一个文件名模式(如 **/*.py),它返回所有匹配的文件路径. 让模型知道所有的配置文件在哪
# 或者所有python文件在哪

name = "glob"

description = (
    "按文件名通配模式查找文件,返回匹配的文件路径列表。"
    "当你想知道某类文件在哪(如所有 .py 文件、某目录下的配置文件)时使用。"
    "参数 pattern 是通配模式,如 '**/*.py' 表示递归查找所有 py 文件。"
)

parameters = {
    "type": "object",
    "properties": {
        "pattern": {"type": "string", "description": "文件名通配模式,如 **/*.py"},
    },
    "required": ["pattern"],
}

def glob(pattern):
    # 1. 用 globlib.glob(pattern, recursive=True) 拿到 list
    # 2. 匹配到了:把路径们拼成一段文本返回(每行一个,用 "\n".join)
    # 3. 一个都没匹配到:返回一句"没找到"的提示(空结果也要让模型看懂)
    matches = globlib.glob(pattern,recursive=True)
    if not matches:
        return f"没有匹配 {pattern} 的文件"
    return "\n".join(matches)

register(Tool(name=name, description=description, parameters=parameters, execute=glob))