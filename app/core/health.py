import sys
import time

from app.core import device, llm

def check() -> tuple[bool, str]:
    try:
        model = llm.resolve_model()
    except Exception as e:
        return False, f"ollama: {e}"
    try:
        answer = llm.chat([{"role": "user", "content": "Reply with one word: ok"}], num_predict=16)
    except Exception as e:
        return False, f"model {model} does not respond: {e}"
    if not answer.strip():
        return False, f"model {model} returned an empty answer"
    return True, model

def wait(timeout: int = 600, step: int = 5) -> tuple[bool, str]:
    deadline = time.time() + timeout
    ok, info = check()
    while not ok and time.time() < deadline:
        print(f"waiting: {info}", flush=True)
        time.sleep(step)
        ok, info = check()
    return ok, info

if __name__ == "__main__":
    ok, info = wait()
    print(f"ollama is ready, model {info}" if ok else f"error: {info}", flush=True)
    if ok:
        print(device.report(), flush=True)
    sys.exit(0 if ok else 1)
