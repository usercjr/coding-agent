import glob as globlib
from agent.tools.base import Tool, register

# load_skill：按名读取某个 skill 的完整正文（渐进式加载的“正文层”）
# parse_frontmatter只读简介，在agent根据简介确定要用skill后再读正文
# loop里面调用available_skills_text()，会把所有的skill简介都记录下来
name = "load_skill"

description = (
    "加载一个技能(skill)的完整操作说明。当你判断当前任务匹配某个技能时,"
    "先调用它拿到该技能的详细流程,再照着执行。参数 skill_name 是技能名。"
)

parameters = {
    "type": "object",
    "properties": {
        "skill_name": {"type": "string", "description": "要加载的技能名,如 code-review"},
    },
    "required": ["skill_name"],
}


def load_skill(skill_name):
    path = f"skills/{skill_name}/SKILL.md"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return f"技能不存在或无法加载:{skill_name}"


# ---------- 简介层：扫描 skills/ 生成“一句话简介”清单 ----------

def _parse_frontmatter(path):
    """从 SKILL.md 头部的 --- 块里抠出 name 和 description。"""
    name = desc = ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return name, desc
    if text.startswith("---"):
        end = text.find("---", 3)          # 找第二个 ---
        block = text[3:end]                # 两个 --- 之间的内容
        for line in block.splitlines():
            if line.startswith("name:"):
                name = line[len("name:"):].strip()
            elif line.startswith("description:"):
                desc = line[len("description:"):].strip()
    return name, desc


def available_skills_text():
    """扫描所有 skill，拼成给 system prompt 用的简介清单。"""
    lines = []
    for path in globlib.glob("skills/*/SKILL.md"):
        name_, desc_ = _parse_frontmatter(path)
        if name_:
            lines.append(f"- {name_}: {desc_}")
    return "\n".join(lines)


register(Tool(name=name, description=description, parameters=parameters, execute=load_skill))
