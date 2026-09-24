from agent.tools.base import Tool, register

# 这是让agent读文件的tool，需要写tool四件套，并且其中的execute负责执行

name = "read_file"

description = (
    "读取指定路径的文本文件，返回其完整内容。"
    "当你需要查看某个文件里写了什么（源码、配置、文档等）时使用。"
    "参数 path 是文件路径。若文件不存在或无法读取，会返回错误说明。"
)

parameters = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "要读取的文件路径"},
    },
    "required": ["path"],
}

def read_file(path):
    # 1. try: 用 with open(path, ...) 打开,读出全部内容,return 它
    #    - 记得指定文本编码,避免中文乱码
    # 2. except: 捕获读文件可能出的错,return 一段错误说明字符串
    #    - 想想:该 except 哪个/哪些异常类型?
    try:
        with open(path, "r", encoding="UTF-8",) as f:
            return f.read()
    except OSError as e: return f"读取失败:{e}"


register(Tool(name=name, description=description, parameters=parameters, execute=read_file))
