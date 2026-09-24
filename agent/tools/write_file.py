from agent.tools.base import Tool, register

# 这是让 agent 写文件的 tool，覆盖写入，文件不存在则创建

name = "write_file"

description = (
    "把给定内容写入指定路径的文件（覆盖原有内容，文件不存在则创建）。"
    "当你需要新建文件或整体替换一个文件的内容时使用。"
    "参数 path 是目标路径，content 是要写入的文本。写入成功会返回确认信息。"
)

parameters = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "要写入的文件路径"},
        "content": {"type": "string", "description": "要写入的文本内容"},
    },
    "required": ["path", "content"],
}

# 使用w写入操作并记录多少个字符的内容已经写入
def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入 {len(content)} 个字符到 {path}"
    except OSError as e:
        return f"写入失败:{e}"


register(Tool(name=name, description=description, parameters=parameters, execute=write_file))
