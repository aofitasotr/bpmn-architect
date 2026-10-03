from app.agents.state import BPMNState
from app.bpmn.validator import validate
from app.core import config

def check(state: BPMNState) -> dict:
    return {"errors": validate(state["mmd"])}

def route(state: BPMNState) -> str:
    if not state["errors"] or state["attempts"] >= config.MAX_ATTEMPTS:
        return "done"
    return "retry"
