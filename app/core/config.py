import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_CANDIDATES = [m for m in os.getenv("OLLAMA_MODELS", "qwen3.5:7b,qwen3.5:9b").split(",") if m]
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", "5"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
NUM_CTX = int(os.getenv("NUM_CTX", "16384"))
NUM_PREDICT = int(os.getenv("NUM_PREDICT", "4096"))
