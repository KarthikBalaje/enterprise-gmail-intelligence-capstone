FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY agent-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY agent-service/app ./app
COPY guardrails ./guardrails
COPY rag-service ./rag_service

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
