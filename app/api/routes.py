from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.agents.graph import run
from app.api.schemas import BPMNRequest, BPMNResponse

router = APIRouter()

@router.get("/")
async def root():
    return {"service": "BPMN Architect AI"}

@router.post("/diagram", response_model=BPMNResponse)
async def diagram(body: BPMNRequest):
    state = await run_in_threadpool(run, body.text, body.previous, body.instruction)
    return BPMNResponse(
        ok=not state["errors"],
        mmd=state["mmd"],
        errors=state["errors"],
        attempts=state["attempts"],
    )
