import re
import glob as globlib
import os
from agent.tools.base import Tool, register

# grep 是“侦察”（找内容在哪），edit 是“动手”（改内容）。
# grep 帮模型看清有几处、各在哪，模型才能给 edit 传出能唯一定位的上下文。

name = "grep"

description = (
    "在文件内容中搜索匹配某个正则模式的行,返回 文件:行号:该行内容。"
    "当你想找某段代码/文字在哪个文件的第几行时使用。"
    "参数 pattern 是正则模式;可选 path 限定搜索范围(文件名通配,默认全项目递归)。"
)

parameters = {
    "type": "object",
    "properties": {
        "pattern": {"type": "string", "description": "要搜索的正则模式"},
        "path": {"type": "string", "description": "限定搜索范围的文件通配,默认 **/*"},
    },
    "required": ["pattern"],
}


def grep(pattern, path="**/*"):
    # 1. 用 glob 把模式展开成真实文件清单（先确定“搜哪些文件”）
    file = globlib.glob(path, recursive=True)
    result = []
    for filepath in file:
        # 只处理真正的文件，跳过目录
        if not os.path.isfile(filepath):
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    if re.search(pattern, line):
                        result.append(f"{filepath}:{lineno}:{line.rstrip()}")
        except (OSError, UnicodeDecodeError):
            # 一个坏文件（权限/二进制乱码）跳过即可，不让整体失败
            continue
    if not result:
        return f"没有匹配 {pattern} 的内容"
    output = "\n".join(result)
    if len(output) > 3000:
        output = output[:3000] + "\n...(结果已截断)"
    return output


register(Tool(name=name, description=description, parameters=parameters, execute=grep))
