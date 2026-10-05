from functools import lru_cache

from ollama import Client

from app.core import config

@lru_cache(maxsize=1)
def client() -> Client:
    return Client(host=config.OLLAMA_HOST)

def installed_models() -> list[str]:
    return [m.model for m in client().list().models]

def resolve_model() -> str:
    available = installed_models()
    for name in config.MODEL_CANDIDATES:
        if name in available or f"{name}:latest" in available:
            return name
    raise RuntimeError(
        f"None of the models {config.MODEL_CANDIDATES} is installed, available: {available}"
    )

def chat(messages: list[dict], num_predict: int | None = None, temperature: float | None = None) -> str:
    response = client().chat(
        model=resolve_model(),
        messages=messages,
        think=config.THINK,
        options={
            "temperature": config.TEMPERATURE if temperature is None else temperature,
            "num_ctx": config.NUM_CTX,
            "num_predict": num_predict or config.NUM_PREDICT,
        },
    )
    return response.message.content or ""
