from app.agents.state import BPMNState


def validate_request(
    state: BPMNState
) -> BPMNState:
    # TODO: заменить на вызов LLM

    response = {
        "valid": True,
        "reason": "Запрос описывает бизнес-процесс"
    }

    return {
        **state,
        "is_valid": response["valid"],
        "validation_reason": response["reason"]
    }


def validation_router(
    state: BPMNState
):
    if state["is_valid"]:
        return "valid"
    return "invalid"