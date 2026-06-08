FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl file libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY file_guard/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY file_guard/app ./app

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8080"]
