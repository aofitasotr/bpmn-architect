# BPMN Architect AI

Агент строит диаграмму в нотации BPMN 2.0, по текстовому описанию. Модель генерирует MMD (далее можно скачать XML), результат проверяется валидатором, при ошибках отправляется на доработку (LangGraph), в браузере рисуется через `app/web/index.html`, где пулы считаются по границам дорожек.

## Требования

### Оборудование

- RAM: не менее 16 ГБ
- Свободное место на диске: не менее 15 ГБ
- CPU: 4 ядра и больше
- GPU: опционально (CUDA/MPS)

### Программное обеспечение

- ОС: macOS, Linux, Windows 10/11 (WSL2 или Docker Desktop)
- Docker 24+ и Docker Compose v2
- Запуск без Docker: Python 3.12 или 3.13 и установленная Ollama
- Браузер: Chrome, Firefox, Safari, Edge

### Сеть

- Интернет при первом запуске: скачивание образов и модели qwen3.5:9b
- Интернет при работе: браузер подгружает Mermaid и Font Awesome с CDN jsdelivr
- Свободные порты: 8501 (интерфейс), 11434 (Ollama)

## Запуск в Docker

Linux, macOS, WSL, Git Bash:

```bash
./docker/up.sh
```

Windows (PowerShell):

```powershell
.\docker\up.ps1
```

Скрипт запускает Docker, если он выключен (Colima, Docker Desktop или systemd), проверяет что ему доступно не меньше 10 ГБ памяти (`DOCKER_MEMORY_GB`, для Colima также `COLIMA_CPU`) и делает `docker compose up --build`. Для Docker Desktop и WSL2 память задаётся в настройках, скрипт подскажет где. Без скриптов достаточно `docker compose up --build`.

`ollama` стартует, `model-pull` скачивает `qwen3.5:9b` (если не получилось - `qwen3.5:7b` если нет, другую), `app` ждёт модель, проверяет что Ollama отвечает, и запускает UI.

UI: http://localhost:8501

## Локально

```bash
pip install -r requirements.txt
python -m app.core.health
streamlit run app/ui/main.py
```

## Структура

- `app/prompts/system.md` - шаблонный запрос: справочник элементов и правила
- `app/prompts/examples/` - рабочие примеры (описание + MMD)
- `app/bpmn/validator.py` - проверка MMD
- `app/agents/` - граф generate -> check -> retry
- `app/web/index.html`, `icons.json` - рендер и расчёт пулов
- `app/ui/main.py` - Streamlit
