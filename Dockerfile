FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/srv
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY .streamlit .streamlit

EXPOSE 8501

CMD ["sh", "-c", "python -m app.core.health && exec streamlit run app/ui/main.py --server.address=0.0.0.0 --server.port=8501"]
