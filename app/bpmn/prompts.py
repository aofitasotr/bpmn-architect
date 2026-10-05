import re
from functools import lru_cache
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
FENCE = re.compile(r"```(?:mermaid|mmd)?\s*\n(.*?)```", re.S)

@lru_cache(maxsize=1)
def system_prompt() -> str:
    parts = [(PROMPTS / "system.md").read_text().strip(), "# EXAMPLES OF WORKING DIAGRAMS"]
    for i, mmd in enumerate(sorted((PROMPTS / "examples").glob("*.mmd")), 1):
        request = mmd.with_suffix(".request.txt").read_text().strip()
        parts.append(f"## Example {i}\nProcess description:\n{request}\n\nAnswer:\n```mermaid\n{mmd.read_text().strip()}\n```")
    return "\n\n".join(parts)

def extract_mmd(text: str) -> str:
    blocks = FENCE.findall(text)
    code = blocks[0] if blocks else text
    return code.strip()

def language_rule(request: str) -> str:
    if re.search("[\u0400-\u04FF]", request):
        return "Write ALL labels (events, tasks, gateways, lanes, pools, flows) in Russian."
    return "Write all labels in the language of the process description."

def build_messages(request: str, previous: str, instruction: str, raw: str, errors: list[str]) -> list[dict]:
    if previous and instruction:
        user = (
            f"Original process description:\n{request}\n\n"
            f"Current diagram:\n```mermaid\n{previous}\n```\n\n"
            f"Apply this change to the diagram: {instruction}\n"
            "Keep the language of the existing labels. "
            "Return the full code of the updated diagram and keep everything else unchanged."
        )
    else:
        user = f"Process description:\n{request}\n\nBuild the diagram. {language_rule(request)}"
    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": user},
    ]
    if errors:
        report = "\n".join(f"- {e}" for e in errors)
        messages += [
            {"role": "assistant", "content": f"```mermaid\n{raw}\n```"},
            {"role": "user", "content": f"The diagram has errors:\n{report}\n\nFix all errors and return the full corrected code in a single ```mermaid block."},
        ]
    return messages
