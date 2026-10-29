# Notification event map

| Event | Получатели | Link |
|---|---|---|
| `request.created` | ответственный и видимые активные контрагенты | `/requests/{request_id}` |
| `request.status_changed` | участники заявки по unit/domain scope | `/requests/{request_id}` |
| `request.files_changed` | ответственный и релевантные авторы предложений | `/requests/{request_id}` |
| `offer.created` / `offer.updated` | участники заявки по policy | request/offer route |
| `message.created` | участники чата | chat route |
| `user.review_required` | admin/superadmin/security officer по target role/source | `/admin/users` или `/contractors` |

Получатели вычисляются из текущего Acom business state, units, visibility и notification preferences. Доступ по ссылке требует действующую IAM session и повторно проверяется backend policy.
