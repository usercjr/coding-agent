from agent.tools.base import Tool, register

# 这是对文件的部分内容进行编辑，把原文的一段精确替换为新的内容

name = "edit_file"

description = (
    "对文件做精确替换:把文件中的 old_string 替换成 new_string。"
    "当你只需修改文件的一小部分、而不是重写整个文件时使用。"
    "参数 path 是文件路径,old_string 是要被替换的原文(必须在文件中唯一匹配),"
    "new_string 是替换后的新内容。"
)

parameters = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "要编辑的文件路径"},
        "old_string": {"type": "string", "description": "要被替换的原文,必须在文件中唯一出现"},
        "new_string": {"type": "string", "description": "替换后的新内容"},
    },
    "required": ["path", "old_string", "new_string"],
}


def edit_file(path, old_string, new_string):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return f"修改失败:{e}"

    count = content.count(old_string)
    if count == 0:
        return "没有找到原文"
    if count > 1:
        return f"匹配到 {count} 处，不唯一，请补充上下文。"

    new_content = content.replace(old_string, new_string)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except OSError as e:
        return f"错误:无法写入文件 {path}: {e}"
    return f"已在 {path} 中完成替换"


register(Tool(name=name, description=description, parameters=parameters, execute=edit_file))
