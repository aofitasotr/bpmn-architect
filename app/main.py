from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="BPMN Architect AI",
    version="0.1.0"
)


app.include_router(router)


@app.get("/health")
async def health():

    return {
        "status": "ok"
    }