# BPMN Architect AI

## Требования

- Python 3.12+
- Poetry


## Установка зависимостей

```bash
poetry install
```

## Запуск приложения

Запуск FastAPI сервера:

```bash
poetry run uvicorn app.main:app --reload
```

После запуска приложение доступно:

```
http://127.0.0.1:8000
```

Документация API:

```
http://127.0.0.1:8000/docs
```