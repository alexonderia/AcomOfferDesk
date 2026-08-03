# Notifications Worker

`notifications_worker` is the asynchronous email-delivery process for AcomOfferDesk.

It connects to RabbitMQ, binds the durable queue `notify.email` to exchange `app.events` with routing key `email.send`, and delivers messages through SMTP. Delivery results are published back as `email.delivery.succeeded` or `email.delivery.failed` events.

## Runtime

```text
backend -> app.events / email.send -> notify.email -> notifications_worker -> SMTP
                                              \-> email delivery result event
```

The worker does not handle in-app or WebSocket delivery; those remain backend responsibilities.

## Main files

```text
app/main.py             RabbitMQ connection and email queue binding
app/consumers.py        Email payload validation and dispatch
app/email_sender.py     SMTP delivery, deduplication, and cooldown
app/result_publisher.py Delivery-result publication
```

## Environment

- `RABBITMQ_URL`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_SECURITY`
- `EMAIL_ADDRESS`
- `EMAIL_APP_PASSWORD`
- `EMAIL_FROM_NAME`
- `EMAIL_DEDUP_TTL_SECONDS`
- `EMAIL_SPAM_COOLDOWN_SECONDS`

## Checks

From the repository root:

```powershell
$env:PYTHONPATH='.;notifications_worker'
.\.venv\Scripts\python.exe -c "import notifications_worker.app.main; import notifications_worker.app.consumers"
.\.venv\Scripts\python.exe -m pytest notifications_worker/tests
```
