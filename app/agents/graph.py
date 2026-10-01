from langgraph.graph import (
    StateGraph,
    END
)

from app.agents.state import BPMNState
from app.agents.nodes.validator import (
    validate_request,
    validation_router
)
from app.agents.nodes.architect import (
    generate_process_model
)
from app.agents.nodes.mermaid import (
    generate_mermaid
)


graph = StateGraph(BPMNState)


graph.add_node(
    "validator",
    validate_request
)

graph.add_node(
    "architect",
    generate_process_model
)

graph.add_node(
    "mermaid",
    generate_mermaid
)


graph.set_entry_point(
    "validator"
)


graph.add_conditional_edges(
    "validator",
    validation_router,
    {
        "valid":"architect",
        "invalid":END
    }
)


graph.add_edge(
    "architect",
    "mermaid"
)

graph.add_edge(
    "mermaid",
    END
)


workflow = graph.compile()