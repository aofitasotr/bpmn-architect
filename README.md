# BPMN Architect AI

Агент строит BPMN 2.0 диаграмму по текстовому описанию. Модель генерирует MMD (Mermaid), результат проверяется валидатором, при ошибках отправляется на доработку (LangGraph), в браузере рисуется через `app/web/index.html`, где пулы считаются по границам дорожек.

## Запуск в Docker

```bash
docker compose up --build
```

Что происходит: `ollama` стартует, `model-pull` скачивает `qwen3.5:7b` (если такой модели нет — `qwen3.5:9b`), `app` ждёт модель, проверяет что Ollama отвечает, и запускает UI.

UI: http://localhost:8501

## Локально

```bash
pip install -r requirements.txt
python -m app.core.health
streamlit run app/ui/main.py
```

## Структура

- `app/prompts/system.md` — шаблонный запрос: справочник элементов и правила
- `app/prompts/examples/` — рабочие примеры (описание + MMD)
- `app/bpmn/validator.py` — проверка MMD
- `app/agents/` — граф generate → check → retry
- `app/web/index.html`, `icons.json` — рендер и расчёт пулов
- `app/ui/main.py` — Streamlit
