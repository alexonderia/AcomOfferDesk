FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY notifications_worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY notifications_worker/app ./app
COPY shared ./shared

CMD ["python", "-m", "app.main"]