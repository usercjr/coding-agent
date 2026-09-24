"""生命周期钩子（事件总线 / 观察者模式）。

在关键节点（pre_tool / post_tool / session_start ...）触发已注册的钩子，
让日志、校验、拦截等横切逻辑不必写进 Agent Loop 核心。

约定：钩子函数收到 context，返回 None = 放行；返回非空字符串 = 拦截（字符串是原因）。
default hook里面记录要加入的hook
"""
# Hook 注册表:事件名 → 钩子函数列表
# 为了让loop里面功能不放那么多，分发出来
# 主要功能：每次 agent 要执行工具前,先记一笔日志register_hook，
# 每次执行工具前,先检查是不是危险命令,是就拦下。fire，把挂在这个时刻的钩子全叫起来"的触发器
_HOOKS = {}


def register_hook(event, fn):
    """把钩子 fn 挂到某个事件上。"""
    # 填这里:把 fn 追加进 _HOOKS[event] 这个列表
    # 用 setdefault:event 第一次出现时列表还不存在,setdefault 会先建空列表再返回
    _HOOKS.setdefault(event, []).append(fn)
    

# context里面放的是即将执行的工具和内容args，{"name": name, "args": args}这就是context
def fire(event, context):
    """触发某事件下所有钩子。任一钩子返回非空(拦截原因)→ 立即返回它;全放行 → 返回 None。"""
    for fn in _HOOKS.get(event, []):      # 取该事件的钩子列表(没有就空列表,不报错)
        #   调 fn(context) 拿返回值, 就是hook中的所有events
        #   如果返回值非空(拦截原因),就 return 它
        reason = fn(context)
        if reason:
            return reason
    return None
                       # 循环走完没人拦截