FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/uploads /app/keycloak

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY infra/keycloak/bootstrap.sh ./keycloak/bootstrap.sh

CMD ["sh", "-c", "exec gunicorn -k uvicorn.workers.UvicornWorker -w ${BACKEND_WORKERS:-1} -b 0.0.0.0:8000 app.main:app"]
