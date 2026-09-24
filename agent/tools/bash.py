from agent.tools.base import Tool, register
import subprocess
# bash 可以让agent执行shell命令，需要瞬间完成，command就是要执行的命令

MAX_OUTPUT = 3000   # 输出最多保留多少字符

name = "bash"

description = (
    "在 shell 中执行一条命令并返回其输出(stdout 和 stderr)。"
    "当你需要运行程序、跑测试、用 git、安装依赖等操作时使用。"
    "参数 command 是要执行的命令字符串。"
)

parameters = {
    "type": "object",
    "properties": {
        "command": {"type": "string", "description": "要执行的 shell 命令"},
    },
    "required": ["command"],
}

def bash(command):
    # 1. try: subprocess.run(...) 跑命令,设一个 timeout(秒)
    # 2. except subprocess.TimeoutExpired: return 超时错误串
    # 3. 拿 result 后:
    #    - 把 stdout 和 stderr 组合成要返回的文本(stderr 也要给模型看,报错信息在里面)
    #    - 如果太长,截断到前 N 个字符(想想怎么截、怎么提示"已截断")
    #    - return 这段文本(可带上 returncode,让模型知道成没成)
    try:
        result = subprocess.run(
            command,
            shell=True,            # 让它按 shell 命令解析(支持管道、重定向等)
            capture_output=True,   # 捕获 stdout 和 stderr
            text=True,             # 输出按字符串返回(不是 bytes)
            timeout=30,            # 秒数;超时会抛 subprocess.TimeoutExpired
        )
        # result.stdout / result.stderr / result.returncode 三样你都能拿到,分别是正常输出，错误输出和退出码
    except subprocess.TimeoutExpired:
        return "错误：命令执行超时（超过30秒）"

    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += "\n[stderr]\n" + result.stderr

    # 太长的情况
    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + "\n ... (输出已截断)"
    
    # 退出码，让模型一眼看出命令成功(0)还是失败(非 0)
    return f"[退出码{result.returncode}]\n{output}"

register(Tool(name=name, description=description, parameters=parameters, execute=bash))