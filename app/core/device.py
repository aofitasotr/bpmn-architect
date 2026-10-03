import platform
import shutil
import subprocess

from app.core import llm


def detect() -> str:
    if shutil.which("nvidia-smi"):
        try:
            subprocess.run(["nvidia-smi", "-L"], check=True, capture_output=True, timeout=5)
            return "cuda"
        except Exception:
            pass
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return "mps"
    return "cpu"


def loaded() -> str:
    try:
        models = llm.client().ps().models
    except Exception:
        return "unknown"
    if not models:
        return "model not loaded"
    total = sum(m.size or 0 for m in models)
    vram = sum(m.size_vram or 0 for m in models)
    if not total or not vram:
        return "cpu"
    return f"gpu {round(100 * vram / total)}%"


def report() -> str:
    return f"host device: {detect()}, ollama runs on: {loaded()}"
