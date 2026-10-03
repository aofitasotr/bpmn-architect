from langgraph.graph import END, StateGraph

from app.agents.nodes.check import check, route
from app.agents.nodes.generate import generate
from app.agents.state import BPMNState

graph = StateGraph(BPMNState)
graph.add_node("generate", generate)
graph.add_node("check", check)
graph.set_entry_point("generate")
graph.add_edge("generate", "check")
graph.add_conditional_edges("check", route, {"retry": "generate", "done": END})
workflow = graph.compile()

def run(request: str, previous: str = "", instruction: str = "") -> BPMNState:
    return workflow.invoke({
        "request": request,
        "previous": previous,
        "instruction": instruction,
        "raw": "",
        "mmd": "",
        "errors": [],
        "attempts": 0,
    })
