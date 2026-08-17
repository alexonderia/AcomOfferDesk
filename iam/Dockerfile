FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY iam/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY iam/iam_app ./iam_app

RUN addgroup --system iam \
    && adduser --system --ingroup iam --home /app --no-create-home iam

USER iam

CMD ["sh", "-c", "exec gunicorn -k uvicorn.workers.UvicornWorker -w ${IAM_WORKERS:-1} -b 0.0.0.0:8100 iam_app.main:app"]
