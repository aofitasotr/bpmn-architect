from app.agents.state import BPMNState
from app.bpmn.repair import repair
from app.bpmn.validator import validate
from app.core import config

def check(state: BPMNState) -> dict:
    mmd = repair(state["mmd"])
    return {"mmd": mmd, "raw": mmd, "errors": validate(mmd)}

def route(state: BPMNState) -> str:
    if not state["errors"] or state["attempts"] >= config.MAX_ATTEMPTS:
        return "done"
    return "retry"
