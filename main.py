from agent.loop import run, set_teach, is_teach
from agent.mcp_client import load_mcp_tools
import agent.default_hooks          # import 即注册示例钩子（审计 + 安全）
from agent.default_hooks import set_auto_approve, is_auto_approve

# 命令 → prompt 模板（prompt 宏那类）
COMMANDS = {
    "review": "请审查以下文件的代码，找出潜在 bug 和改进点：{arg}",
    # 以后加 "commit": "...", "explain": "..." 都往这加
}


def handle_slash(user_input):
    """处理斜杠命令。返回 True 表示已处理（外层应 continue）。"""
    parts = user_input[1:].split(maxsplit=1)   # 去掉 /，拆成 [命令, 参数]
    cmd = parts[0]
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "help":
        # 动作类：直接打印有哪些命令，不进模型
        print("可用命令：")
        print("  /help          显示本帮助")
        print("  /review <文件>  审查指定文件的代码")
        print("  /auto          切换自动批准（开=不再弹确认）")
        print("  /teach         切换教学模式（开=当陪练导师，不代写）")
    elif cmd == "auto":
        set_auto_approve(not is_auto_approve())          # 切换开关
        print(f"自动批准已{'开启（不再弹确认）' if is_auto_approve() else '关闭'}")
    elif cmd == "teach":
        set_teach(not is_teach())                        # 切换教学模式
        print("教学模式已" + ("开启（我会当陪练导师，不直接代写）" if is_teach() else "关闭"))
    elif cmd in COMMANDS:
        # prompt 宏：查表 → 展开 → 进模型
        prompt = COMMANDS[cmd].format(arg=arg)
        run(prompt)
    else:
        print(f"未知命令：/{cmd}（输入 /help 查看可用命令）")
    return True


if __name__ == "__main__":
    load_mcp_tools()                       # 启动时注册一次 MCP 工具（较慢，稍等几秒）
    print("Coding Agent（输入 exit 退出，/help 查看命令）")
    while True:
        user_input = input("\n你> ")
        if user_input.strip() in ("exit", "quit"):
            break
        if user_input.startswith("/"):
            handle_slash(user_input)
            continue                       # 斜杠命令已处理，跳过下面的普通输入
        run(user_input)
