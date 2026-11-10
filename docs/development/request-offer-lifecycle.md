# Request–Offer Lifecycle

## Выбор контрагента при ручном создании КП

`GET /api/v1/requests/{request_id}/offers/manual/eligible-contractors` возвращает
активных контрагентов в области заявки с учётом lifecycle и скрытых контрагентов.
Контрагенты, у которых уже есть неудалённое КП по этой заявке, остаются в списке:
сервер возвращает для них `can_select=false` и `disabled_reason` с пояснением
«Данный контрагент уже приложил КП к текущей заявке». Остальные записи имеют
`can_select=true` и `disabled_reason=null`; удалённое КП не блокирует выбор.

В диалоге недоступные записи нельзя выбрать мышью или клавиатурой. Пояснение
отображается в строке и во всплывающей подсказке при наведении или долгом нажатии.
Отсутствующий `can_select` не разрешает выбор. Сервер при создании КП независимо
повторно проверяет доступ и отклоняет дубликат с `409 Conflict`.

В режиме «Создать нового» поиск похожих контрагентов работает по названию,
ИНН и e-mail с задержкой 350 мс. Для него используется
`GET /api/v1/requests/{request_id}/offers/manual/contractor-duplicates`:
сервер проверяет `offers.manual.create` и область текущей заявки, не требуя
отдельного `contractors.manual.create`. Поиск использует общий механизм
поиска дублей справочника. Ответ включает `can_select` и `disabled_reason`;
контрагент с существующим КП виден, но недоступен для выбора.
Кнопка «Использовать этого контрагента» переводит диалог в выбор существующего
контрагента, сохраняя сумму и приложенные файлы. Устаревшие ответы поиска
после изменения данных, заявки или закрытия формы игнорируются; ошибка поиска
показывается отдельно от отсутствия совпадений.
Даты создания и изменения в карточках дублей отображаются с точностью до минут,
без секунд и дробной части.

При создании нового контрагента вместе с КП используется общий сервис ручного
контрагента: он создаёт IAM account и IAM-привязку даже без почты и пароля.
Повторное использование компании синхронизирует отсутствующую identity, сохраняя
существующие credentials и ограничения доступа. При недоступности IAM создание
КП не завершается успешно, локальные изменения откатываются через UnitOfWork.
Общий контракт и повтор после частичного сбоя описаны в
[регистрации и онбординге](../security/auth-and-onboarding.md#ручное-создание).

## Scenario: chosen Offer, close, and savings dashboard

### 1. Scope / Trigger

- Trigger: a staff user accepts an Offer, changes `Request.final_amount`, closes a Request, or reads its Offer actions / Savings Dashboard data.
- This is a backend-owned cross-layer contract. The frontend renders the persisted API values and does not reselect an Offer or authorise mutations.

### 2. Signatures

- `OfferService.update_status(current_user, offer_id, status) -> str`
- `OfferService.update_amount(current_user, offer_id, offer_amount) -> float`
- `RequestService.update_request(current_user, request_id, data) -> None`
- `RequestRepository.lock_offer_lifecycle(request_id)` uses `request-offer-lifecycle:<request_id>` for the transaction-scoped advisory lock.
- `RequestRepository.has_accepted_offer_for_request(request_id, exclude_offer_id=None) -> bool`
- `GET /api/v1/requests/{request_id}` and `GET /api/v1/offers/{offer_id}/workspace` return Offer `actions`.

### 3. Contracts

- One Request has at most one Offer with `status="accepted"`. A second `accepted` transition is rejected; do not silently reject or mutate the already accepted Offer.
- `Request.id_offer` is the persisted chosen Offer reference for a closed Request. It is assigned atomically at close from the accepted Offer of the same Request, together with `status="closed"` and `closed_at`.
- Accepting an Offer neither closes the Request nor overwrites `final_amount`.
- Close validation for non-zero initial amount:
  - without accepted Offer, `final_amount == initial_amount`;
  - with accepted Offer, `final_amount == initial_amount` or `final_amount == accepted_offer.offer_amount`.
- Dashboard obtains Offer data only through `Request.id_offer` using an outer join. A closed Request without a chosen Offer stays in `closed_items`; every `closed_items[].savings_amount` is numeric, with `0` for a non-applicable calculation.
- Savings branches:
  - `final == chosen_offer.amount` -> `initial - final` (may be negative factual overrun);
  - `final == initial` and `chosen_offer.amount <= initial` -> `chosen_offer.amount - initial` (negative value is lost savings; equality is zero);
- `final == initial` and `chosen_offer.amount > initial` -> `0` in the general closed dataset and omit from calculated savings.
- Offer mutation action flags (`edit amount`, status actions, delete, file actions) are false for parent Request `closed` or `cancelled`; backend services enforce the same restriction authoritatively.

### 4. Validation & Error Matrix

| Condition | Result |
|---|---|
| A different Offer of the same Request is already accepted | `409 Conflict`: `Для заявки уже выбрано принятое КП`; no status mutation or success event |
| Offer status/amount mutation races close | Both acquire the same lifecycle lock; one transaction sees the final state and either succeeds consistently or returns `409` |
| Close final amount is neither initial nor accepted Offer amount | `409 Conflict`; UoW rolls back the whole request mutation |
| Parent Request is closed/cancelled | Offer mutation returns `409`; action flags are false |

### 5. Good/Base/Bad Cases

- Good: initial `1_000_000`, accepted Offer `850_000`, final `850_000` -> Request stores that Offer ID; savings is `150_000`.
- Base: accepted Offer `850_000`, final `1_000_000` -> close succeeds; the Offer remains chosen and lost savings is `-150_000`.
- Bad: accept a second Offer, infer a different Offer during Dashboard GET, auto-replace final amount on accept, or let an Offer above initial create lost savings when final remains initial.

### 6. Tests Required

- Integration: accepted Offer close with final equal to Offer and final equal to initial; reject invalid third amount; assert `id_offer` persists.
- Integration: second accept returns `409`, leaves the target Offer unchanged, and uses the lifecycle lock; amount mutation also acquires the lock.
- Unit: savings covers factual saving, lost saving, ignored above-initial Offer, zero/equal case, and factual overrun.
- Unit/API: action flags hide all offer mutations for closed/cancelled parent and hide accept when another Offer is accepted.
- Manual: `WORK-002`, `REQ-005`, and `DASH-002` verify complete reload consistency.

### 7. Wrong vs Correct

#### Wrong

- Treat the latest accepted Offer as a dashboard read-time choice, expose `can_accept` when the service will reject it, or use a separate lock for close and Offer mutation.

#### Correct

- Persist the chosen Offer at close, use it as the only closed-history reference, project actionable backend flags, and serialize lifecycle writes with one request-scoped advisory lock.
