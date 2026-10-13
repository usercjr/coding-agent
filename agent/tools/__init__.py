"""导入所有工具模块，触发它们的 register()，让工具登记进注册表。

只要 `import agent.tools`（Python 会自动执行本文件），6 个工具就全部注册好。
base 会被各工具模块 `from agent.tools.base import ...` 带着自动加载，无需单独导入。
"""

from . import read_file, write_file, edit_file, bash, glob, grep, load_skill, remember, dispatch, dispatch_parallel
