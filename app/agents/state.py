from typing import TypedDict


class BPMNState(TypedDict):
    user_input: str
    is_valid: bool
    validation_reason: str
    process_model: dict
    mermaid: str