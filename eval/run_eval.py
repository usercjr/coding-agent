import os, subprocess, tempfile, shutil
from agent.loop import run_subagent
from agent.workdir import set_cwd
from eval.cases import CASES
from agent.loop import client   # 复用 loop 里建好的 DeepSeek client

def check_exec(case, workdir):
    # 在临时目录里跑 check 命令,看输出含不含 expect
    r = subprocess.run(case["check"], shell=True, cwd=workdir,
                       capture_output=True, text=True)
    # 👇 你填:输出 r.stdout 里包含 case["expect"] 就算通过,返回 True/False
    return case["expect"] in r.stdout
    


def check_judge(case, output):
    prompt = (
        f"任务:{case['task']}\n\n"
        f"agent 的输出:\n{output}\n\n"
        f"判据:{case['rubric']}\n\n"
        f"请根据判据判断 agent 是否完成任务。只回答一个词:PASS 或 FAIL。"
    )
    resp = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}])
    verdict = resp.choices[0].message.content   # 接住 judge 的回答
    return "PASS" in verdict.upper()

def run_one(case):
    workdir = tempfile.mkdtemp(prefix="eval-")   # 每题一个独立临时目录(隔离)
    try:
        # 预置 seed 起始文件
        for fname, content in case.get("seed", {}).items():
            with open(os.path.join(workdir, fname), "w", encoding="utf-8") as f:
                f.write(content)
        set_cwd(workdir)                 # 让 agent 的工具都落到这个临时目录(复用 contextvars)
        output = run_subagent(case["task"])
        if case["kind"] == "exec":
            return check_exec(case, workdir)
        else:
            return check_judge(case, output)
    finally:
        set_cwd(None)                    # 复位工作目录
        shutil.rmtree(workdir, ignore_errors=True)   # 清理临时目录


def main():
    results = [(c["id"], run_one(c)) for c in CASES]
    for cid, ok in results:
        print(f"{'PASS' if ok else 'FAIL'}  {cid}")
    # 👇 你填:算成功率 = 通过数 / 总数,打印出来
    passed = sum(1 for _, ok in results if ok)
    print(f"成功率: {passed}/{len(results)} = {passed/len(results)*100:.0f}%")
    


if __name__ == "__main__":
    main()