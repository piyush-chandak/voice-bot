import os

PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_prompt_template(name: str) -> str:
    path = os.path.join(PROMPTS_DIR, "prompts", f"{name}.txt")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_system_prompt() -> str:
    return get_prompt_template("system")


def get_summarize_prompt(report: str) -> str:
    template = get_prompt_template("summarize")
    return template.format(report=report)
