#!/bin/sh
set -e
for model in $(echo "${OLLAMA_MODELS:-qwen3.5:7b,qwen3.5:9b}" | tr ',' ' '); do
  if ollama pull "$model"; then
    echo "loaded $model"
    ollama list | grep -q "${model%%:*}" && exit 0
  fi
  echo "No $model found. trying next"
done
echo "Cant load models"
exit 1
