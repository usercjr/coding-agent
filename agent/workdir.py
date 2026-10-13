"""每线程独立的“当前工作目录”机制（给并行 worktree 用）。

线程共享进程 CWD、不能各自 os.chdir；用 contextvars.ContextVar 让每个线程
各持一份自己的工作目录，把每个子 agent 的文件操作路由到它自己的 worktree。
"""

import contextvars
import os

_cwd = contextvars.ContextVar("cwd", default=None)   # 每线程独立的“当前工作目录”


def set_cwd(path):
    # 设置本线程的工作目录
    _cwd.set(path)


def get_cwd():
    # 取本线程的工作目录；没设过就返回项目根
    return _cwd.get() or os.path.realpath(".")


def resolve(path):
    # 把工具收到的相对 path 拼到当前工作目录下（path 已是绝对路径则原样用）
    return os.path.join(get_cwd(), path)
