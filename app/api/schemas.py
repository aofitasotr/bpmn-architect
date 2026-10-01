from pydantic import BaseModel


class BPMNRequest(BaseModel):
    text: str


class BPMNResponse(BaseModel):
    valid: bool
    reason: str
    mermaid: str | None