from app.agents.state import BPMNState
from app.bpmn.prompts import build_messages, extract_mmd
from app.core import config, llm

def generate(state: BPMNState) -> dict:
    messages = build_messages(
        state["request"], state["previous"], state["instruction"], state["raw"], state["errors"]
    )
    answer = llm.chat(messages, temperature=min(0.8, config.TEMPERATURE + 0.2 * state["attempts"]))
    mmd = extract_mmd(answer)
    return {"raw": mmd, "mmd": mmd, "attempts": state["attempts"] + 1}
