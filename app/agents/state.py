from typing import TypedDict

class BPMNState(TypedDict):
    request: str
    previous: str
    instruction: str
    raw: str
    mmd: str
    errors: list[str]
    attempts: int
