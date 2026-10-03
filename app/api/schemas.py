from pydantic import BaseModel

class BPMNRequest(BaseModel):
    text: str
    previous: str = ""
    instruction: str = ""

class BPMNResponse(BaseModel):
    ok: bool
    mmd: str
    errors: list[str]
    attempts: int
