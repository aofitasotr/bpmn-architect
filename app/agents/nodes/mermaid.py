from app.agents.state import BPMNState


def generate_mermaid(
    state: BPMNState
) -> BPMNState:
    # TODO: LLM -> mermaid
    model = state["process_model"]
    result = [
        "flowchart TD"
    ]

    for node in model["nodes"]:
        result.append(
            f'{node["id"]}[{node["name"]}]'
        )

    for flow in model["flows"]:
        result.append(
            f'{flow["from"]} --> {flow["to"]}'
        )

    return {
        **state,
        "mermaid": "\n".join(result)
    }