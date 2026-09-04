# REQ-003 — закрытие Request и итоговая сумма

## Цель

Проверить правила закрытия Request через `PATCH /api/v1/requests/{request_id}`.
Backend является источником истины; клиентская проверка только предотвращает
очевидно некорректную отправку и отображает ошибку API.

## Предусловия

- Пользователь имеет права на редактирование и изменение статуса своей заявки.
- Создание Request без `initial_amount` запрещено; `0` — допустимое заданное значение.
- Заявка открыта, её `final_amount` уже сохранён либо передаётся в том же PATCH.
- `submitted` Offer считается неразрешённым и блокирует закрытие.

## Полный тест-кейс

| ID | Данные Request / Offer | Действие | Ожидаемый результат |
| --- | --- | --- | --- |
| REQ-003-A | `initial_amount=100`, принят Offer `offer_amount=80`, `final_amount=100` | PATCH `status=closed` | 200; Request закрыт, выбран принятый Offer |
| REQ-003-B | `initial_amount=100`, принят Offer `offer_amount=80`, `final_amount=80` | PATCH `status=closed` | 200; Request закрыт, выбран принятый Offer |
| REQ-003-C | `initial_amount=100`, принят Offer `offer_amount=80`, `final_amount=90` | PATCH `status=closed` | 409; `status`, `closed_at`, `id_offer` не изменены |
| REQ-003-D | `initial_amount=100`, принятого Offer нет, `final_amount=100` | PATCH `status=closed` | 200; Request закрыт |
| REQ-003-E | `initial_amount=100`, принятого Offer нет, `final_amount=90` | PATCH `status=closed` | 409; `status`, `closed_at`, `id_offer` не изменены |
| REQ-003-F | `initial_amount=100`, принят Offer без `offer_amount`, `final_amount=100` | PATCH `status=closed` | 200; исходная сумма остаётся допустимой |
| REQ-003-G | `initial_amount=0`, `final_amount=123.45` | PATCH `status=closed` | 200; положительная сумма допустима |
| REQ-003-H | `initial_amount=0`, `final_amount=0` | PATCH `status=closed` | 409; Request остаётся открытым |
| REQ-003-I | Любая иначе допустимая сумма, есть `submitted` Offer | PATCH `status=closed` | 409; Request остаётся открытым |

Для ненулевого `initial_amount` допустимы только исходная сумма и, если у
принятого Offer указана сумма, сумма этого Offer. Для нулевого `initial_amount`
допустима любая положительная `final_amount`.
