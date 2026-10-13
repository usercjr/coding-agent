"""评测集：每道题一个 dict。

kind="exec"  → 确定性检查：跑 check 命令，输出里含 expect 即通过。
kind="judge" → LLM-as-Judge：把 task+结果+rubric 交给 LLM 判通过/不通过。
seed         → 可选，跑题前先在临时工作目录里预置的起始文件 {文件名: 内容}。

扩展说明：题目要尽量"可执行验证(exec)"；judge 只用于没法执行判的开放式题。
覆盖：写代码 / 修 bug / 读+统计+写 / 多条件逻辑 / 开放式解释。
"""

CASES = [
    # ---------- 写代码类(exec) ----------
    {
        "id": "factorial",
        "task": "在 fact.py 里写一个函数 factorial(n) 计算 n 的阶乘。",
        "kind": "exec",
        "check": 'python -c "from fact import factorial; print(factorial(5))"',
        "expect": "120",
    },
    {
        "id": "reverse_string",
        "task": "在 su.py 里写一个函数 reverse_string(s),返回字符串 s 的反转。",
        "kind": "exec",
        "check": 'python -c "from su import reverse_string; print(reverse_string(\'hello\'))"',
        "expect": "olleh",
    },
    {
        "id": "is_palindrome",
        "task": "在 pal.py 里写 is_palindrome(s),判断字符串是否回文,返回 True/False。",
        "kind": "exec",
        "check": 'python -c "from pal import is_palindrome; print(is_palindrome(\'level\'), is_palindrome(\'python\'))"',
        "expect": "True False",
    },
    {
        "id": "fizzbuzz",
        "task": "在 fb.py 里写 fizzbuzz(n):n 能被 3 整除返回 'Fizz',被 5 整除返回 'Buzz',同时被 3 和 5 整除返回 'FizzBuzz',否则返回 str(n)。",
        "kind": "exec",
        "check": 'python -c "from fb import fizzbuzz; print(fizzbuzz(15), fizzbuzz(3), fizzbuzz(5), fizzbuzz(7))"',
        "expect": "FizzBuzz Fizz Buzz 7",
    },
    {
        "id": "sum_even",
        "task": "在 se.py 里写 sum_even(nums),返回列表 nums 中所有偶数之和。",
        "kind": "exec",
        "check": 'python -c "from se import sum_even; print(sum_even([1,2,3,4,5,6]))"',
        "expect": "12",
    },
    {
        "id": "fibonacci",
        "task": "在 fib.py 里写 fib(n):斐波那契数列,约定 fib(0)=0、fib(1)=1。",
        "kind": "exec",
        "check": 'python -c "from fib import fib; print(fib(10))"',
        "expect": "55",
    },

    # ---------- 修 bug 类(exec + seed) ----------
    {
        "id": "fix_add",
        "task": "calc.py 里的 add(a,b) 现在返回 a-b,是个 bug。把它改成正确的加法。",
        "kind": "exec",
        "check": 'python -c "from calc import add; print(add(2,3))"',
        "expect": "5",
        "seed": {"calc.py": "def add(a, b):\n    return a - b\n"},
    },
    {
        "id": "fix_max",
        "task": "mx.py 里的 my_max(lst) 应返回列表最大值,但现在直接返回了第一个元素,是 bug。修好它。",
        "kind": "exec",
        "check": 'python -c "from mx import my_max; print(my_max([3,1,4,1,5,9,2]))"',
        "expect": "9",
        "seed": {"mx.py": "def my_max(lst):\n    return lst[0]\n"},
    },

    # ---------- 读+统计+写(exec) ----------
    {
        "id": "count_lines",
        "task": "读取 data.txt,数出它有多少行,把这个数字(只有数字)写进 answer.txt。",
        "kind": "exec",
        "check": 'python -c "print(open(\'answer.txt\').read().strip())"',
        "expect": "4",
        "seed": {"data.txt": "apple\nbanana\ncherry\ndate\n"},
    },

    # ---------- 开放式解释(judge) ----------
    {
        "id": "explain_recursion",
        "task": "用一两句话解释什么是递归(recursion),给初学者看。",
        "kind": "judge",
        "rubric": "正确解释了递归=函数调用自身,且提到要有终止条件(base case)或类似意思;表达清楚、面向初学者。",
    },
    {
        "id": "explain_closure",
        "task": "用一两句话解释什么是闭包(closure)。",
        "kind": "judge",
        "rubric": "正确说明闭包=函数记住并能访问其定义时所在作用域的变量(即使外层函数已返回);表达基本准确。",
    },
]
