EXCHANGE = "app.events"

QUEUE_EMAIL = "notify.email"
QUEUE_EMAIL_DELIVERY = "notify.email.delivery"
QUEUE_NOTIFY_PROCESS = "notify.process"
# LEGACY: Telegram queue is kept for rollback compatibility.
QUEUE_TG = "notify.tg"
QUEUE_MAX = "notify.max"

RK_EMAIL = "email.send"
RK_EMAIL_DELIVERY_SUCCEEDED = "email.delivery.succeeded"
RK_EMAIL_DELIVERY_FAILED = "email.delivery.failed"
RK_NOTIFICATION_PROCESS = "notification.process"
# LEGACY: Telegram routing key is kept for rollback compatibility.
RK_TG = "telegram.send"
RK_MAX = "max.send"
