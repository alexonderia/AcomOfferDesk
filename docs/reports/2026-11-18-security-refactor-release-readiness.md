# Аудит, рефакторинг и готовность к деплою — 2026-11-18

Версия: ветка `dev`, исходный commit `06567a4`, рабочие изменения текущей сессии.
Исходное рабочее дерево чистое. Окружение: Windows, Python 3.12.10,
Node.js 24.15.0 / npm 11.12.1, локальные unit/API contract tests;
целевой стенд Acom не запущен.

## Согласованный план

Пользователь подтвердил: аудит приложения → исправление подтверждённых проблем
безопасности и бизнес-логики у существующих владельцев поведения → регрессионные
проверки → заключение о готовности к деплою. Отдельная перестройка архитектуры
не входит в согласованный объём. Deploy, commit, push, seed и изменение реальных
данных не выполняются.

1. Проверить IAM/BFF/CSRF, permissions и resource scope, жизненный цикл заявок
   и КП, файлы, уведомления, зависимости и конфигурацию релиза.
2. Устранить подтверждённые обходы доступа, нарушения lifecycle и пробелы проверок.
3. Запустить текущие тесты backend, IAM, file guard, frontend и статические проверки.
4. Зафиксировать взаимосвязи проблем, остаточные риски и обязательные проверки стенда.

## Статус

**Production: NO-GO до завершения проверок целевого стенда.**
Согласованный аудит и исправления выполнены; локальные проверки изменённой
версии прошли. Это основание для проверки release candidate на изолированном
стенде с копией БД. Подтверждения реального rollout, PostgreSQL-конкурентности,
сетевого периметра и браузерных сценариев на целевом окружении пока нет.

Схема и существующие миграции не изменены. Commit, push, deploy, repair/seed,
обращения с изменением реальных данных не выполнялись. Локальное Python-окружение
обновлено согласно изменённым зависимостям; установка совместима по `pip check`.

## Подтверждённые проблемы и исправления

Приоритеты ниже — оценка влияния на данное приложение, без присвоения CVSS.
P1 требует исправления до релиза; P2 — нарушение контракта или надёжности.

| ID | Приоритет | Условие и влияние исходной версии | Исправление |
|---|---|---|---|
| F01 | P1 | Пользователь с `offers.manual.create` из другой ветви оргструктуры мог обратиться непосредственно к ручному созданию КП, списку контрагентов и поиску дублей: service проверял право и особое ограничение экономиста, но не общую область заявки. | Все три пути используют общую проверку `StaffAccessScopeService`; тесты проверяют `403` для другой ветви. |
| F02 | P1 | Ручное создание КП не брало lifecycle/pair lock обычного создания: проверка `open` и отсутствия дубля могла устареть до записи. | Общие `request-offer-lifecycle` и `contractor-offer` advisory locks до проверок. |
| F03 | P1 | Изменение файлов КП и обновление сумм заявки без статуса не синхронизировались с закрытием. Проверка до ожидания другой транзакции не гарантировала итоговый invariant. | Файлы КП блокируют lifecycle и перечитывают состояние/область; все обновления заявки используют тот же lock. |
| F04 | P1 | Удалённое КП сохраняло пути редактирования и возврата в `accepted/rejected`; UI запрещал не все изменения. Это позволяло восстановить старое КП после создания нового. | Удаление — терминальное состояние для mutation; запрет в service и во всех mutation action flags. |
| F05 | P1 | Проверка `value < 0` пропускала `NaN`/Infinity и не учитывала предел `NUMERIC(14,2)`. Результат — некорректные суммы, ошибки сравнения/сериализации/записи и расчётов. | Общая domain-проверка для Request, Offer, Plan: конечное число от 0 до `999999999999.99`; контролируемая ошибка до persistence. |
| F06 | P1 | Команды открытого WebSocket использовали старый auth context. Проверка получателей брала роль из `users.id_role` и не проверяла текущие IAM auth status/required actions. | Повторная проверка активного профиля/привязки и IAM role/status/permissions перед командами и рассылкой; неизвестные значения и недоступность IAM отклоняются. |
| F07 | P2 | `typing.start/stop` позволяли публиковать событие в произвольный chat ID без проверки права отправки. | Перед публикацией используется существующая проверка chat context с `require_send=True`. |
| F08 | P1 | TTL одноразового WS-билета ограничивал только подключение. Уже открытый transport мог пережить access JWT и продолжать получать события. | JWT `exp` передаётся через внутренний auth context в билет; срок билета ограничен JWT, соединение закрывается с `4401` не позднее этого срока. |
| F09 | P2 | После `4401` frontend выполнял refresh, но effect не переподключал transport, если `authenticated/businessAccess` не менялись. | Владелец соединения реагирует на обновлённую session; существующий `connect()` сохраняет идемпотентность. Добавлена регрессия. |
| F10 | P1 | Проверка опасных Office relationships через regex зависела от порядка атрибутов и двойных кавычек; `file:` мог обходить проверку. | Разбор XML через `defusedxml`, обработка namespace/character references, отказ при повреждённом XML/entities. Это нарушение фильтрации документов; выполнение кода на backend не воспроизводилось. |
| F11 | P2 | На Windows `ZipInfo.filename` нормализовал обратные слеши до проверки ZIP path. Исходные опасные имена терялись; тестовая запись ZIP также нормализовала fixtures. | Проверяется `orig_filename`; fixtures сохраняют исходные байты. На Linux исходный пример с обратными слешами уже отклонялся. |
| F12 | P1 | Release script по умолчанию выполнял IAM seed/repair, меняя права во время проверки. | Repair только по явному флагу; Bash дополнительно исключает случайное наследование `IAM_RBAC_REPAIR` в режиме чтения. |
| F13 | P1 | Gate не запускал IAM/file guard tests. RBAC report не сравнивался с ожидаемой матрицей; reconciliation без strict возвращал успех при drift. | Добавлены service test scripts и CI job; `--report --strict` сверяет RBAC, `check-iam.*` включает strict для обеих проверок. |
| F14 | P2 | Локальный `.env` с `EMAIL_ENABLED=false` менял исходные условия почтовых тестов: первый прогон дал 12 unit и 17 integration failures. | Тестовый bootstrap задаёт email-enabled default; no-mail tests явно переключают режим. После исправления оба набора проходят. |

Основные владельцы поведения:
[OfferService](../../backend/app/services/offers.py),
[RequestService](../../backend/app/services/requests.py),
[amounts](../../backend/app/domain/amounts.py),
[ChatRealtimeService](../../backend/app/services/chat_realtime.py),
[WebSocket API](../../backend/app/api/v1/ws.py),
[Office validation](../../file_guard/app/office_security.py),
[RBAC gate](../../backend/app/scripts/seed_iam_rbac.py),
[RealtimeProvider](../../web/src/app/providers/RealtimeProvider.tsx).

## Взаимосвязи

| Связь | Последствие | Защита после исправления |
|---|---|---|
| Функциональное право → resource scope → ручное КП → файлы/уведомления | Пропуск scope на одном endpoint открывает действия и сведения, скрытые обычным списком заявок. | Единый service guard для создания, eligible list и duplicates. |
| Ручное/обычное создание → проверка дубля → принятие → закрытие | Разные блокировки или отсутствие lock позволяют разойтись статусу, выбранному КП и истории. | Общий lifecycle lock, pair lock, перечитывание состояния; удалённое КП не восстанавливается. |
| Суммы Request/Offer → закрытие → `id_offer` → dashboard/планы | Нечисловые или непомещающиеся суммы нарушают несколько модулей одновременно. | Общая domain-валидация; прежние правила выбора КП и расчёта экономии сохраняются. |
| IAM роль/статус/grants → долгоживущий WS → chat scope → доставка | HTTP-защита не прекращает автоматически доступ уже открытого transport. | Проверки identity и scope при командах/рассылке плюс конечный срок соединения; UI восстанавливается после refresh. |
| Upload → file guard → storage → скачивание/предпросмотр | Fail-closed по доступности сканера не исправляет обход внутри самого валидатора XML. | Семантический разбор XML и исходных ZIP-имён до сохранения, обновлённые parser dependencies. |
| Release gate → IAM matrix → runtime enforcement | Автоисправление скрывает исходный drift; отсутствие service tests даёт ложный зелёный результат. | Read-only default, строгая сверка и расширенный набор тестов. |

## Проверки изменённой версии

Все перечисленные результаты получены в этой сессии после соответствующих
изменений, включая обновление зависимостей. Исторические отчёты не использовались
как доказательство успешной проверки.

| Проверка | Результат |
|---|---|
| `scripts/test-unit.ps1` | **704 passed** |
| `scripts/test-integration.ps1` | **372 passed** |
| `scripts/test-iam.ps1` | **98 passed** |
| `scripts/test-file-guard.ps1` | **83 passed**, без skip |
| `npm --prefix web run test:unit` | **495 passed**, 86 файлов |
| `npm --prefix web run lint` | PASS |
| `npm --prefix web run build` | PASS, TypeScript и production Vite build |
| `scripts/check_docs.py`, `scripts/check_mojibake.py` | PASS |
| `python -m pip check` | PASS |
| PowerShell Parser для scripts, `bash -n` изменённых shell scripts | PASS |
| Compose config: dev, test, prod-like, prod overlays | PASS |
| Разбор полученного Compose | В test/prod-like/prod публикуется только gateway; `project_net` external; file guard не получает DB/IAM/S3/SMTP/RabbitMQ secrets |
| `git diff --check` | PASS |

Итого: **1752 теста прошли**. После обновления зависимостей pytest сообщает
предупреждение Starlette о будущем переходе TestClient с httpx на httpx2;
IAM дополнительно предупреждает о deprecated Argon2 version attribute.

Новые проверки покрывают denial для чужой ветви, повторную проверку после
ожидания lock, терминальность удалённого КП, неконечные/слишком большие суммы,
IAM block/role/required actions, WS-команды без доступа, срок билета/соединения,
reconnect и XML-варианты обхода. Моделирование конкурентности использует fakes;
реальные блокировки PostgreSQL этими тестами не подтверждены.

## Зависимости и остаточные advisory

Обновлены согласованно FastAPI/Starlette/AnyIO, python-multipart, python-jose,
pypdf/Pillow; добавлен defusedxml. Frontend обновлён до исправленных Router/Zod
и совместимого resolver; lockfile обновлён. TypeScript-адаптация затрагивает
формы и удалённые Router v6 future props в тестах, без добавления нового UI.

| Аудит | Исходное состояние | Итог |
|---|---|---|
| `npm audit`, весь dependency tree | 26 затронутых пакетов | **10 high**, все в dev/build цепочке picomatch |
| `npm audit --omit=dev` | В исходном lockfile были Router/Zod advisory | **0** |
| `pip-audit`, прямые точные pins всех Python manifests | anyio, Pillow, pypdf, python-jose имели advisory | Только **python-jose 3.5.0**, один advisory без опубликованного исправления |
| `pip-audit`, установленное объединённое `.venv` | 14 затронутых пакетов | 5: python-jose, ecdsa, pip, pytest, setuptools; в отчёте API есть повторные записи advisory |

Оценка применимости оставшихся проблем:

- [python-jose DER algorithm confusion](https://github.com/advisories/GHSA-3qf3-8w2g-rqmx):
  advisory описывает обход при отсутствии явного ограничения algorithms.
  Acom явно требует `RS256`, проверяет header и RSA PEM key; regression
  `test_rejects_unknown_kid_and_symmetric_algorithm` проходит. Вывод аудита:
  описанный путь не обнаружен в текущем IAM access-token verifier. Сам пакет
  остаётся затронутым; waiver или замена JWT-библиотеки требуют отдельного
  зафиксированного решения перед production.
- [ecdsa Minerva](https://github.com/advisories/GHSA-wj6h-64fc-37mp):
  относится к ECDSA signing/key generation/ECDH; проверка подписи не затронута.
  В просмотренных IAM signing paths используется RSA. Это оценка применимости
  текущих путей, а не утверждение об исправлении транзитивного пакета.
- [picomatch ReDoS](https://github.com/advisories/GHSA-fc5q-39xc-vjpf):
  исправленная версия не опубликована. Пакет находится в lint/test/build tools;
  production web отдаёт собранную статику nginx. Шаблоны glob в текущем проекте
  задаются репозиторием; обработка атакующего glob через UI не найдена.
  Нужны доверенные inputs сборки и зафиксированное решение по CI-риску.
- pip/pytest/setuptools — замечания к локальному toolchain; они не являются
  доказанными уязвимостями API приложения. Образы контейнеров и их toolchain
  требуют отдельного сканирования. В отчёте `.venv` смешаны runtime и test tools.

Формальные dependency audits с оставшимися advisory возвращают ненулевой код.
Они **не объявляются пройденными**. Без исправления upstream или явно принятого
и документированного исключения требование «нулевой полный audit» не выполнено.

## Что ещё требуется для production

1. Собрать реальные Linux-образы release candidate и проверить их dependency/OS
   состав. Версии Python transitive dependencies полностью не зафиксированы;
   локальное `.venv` не заменяет SBOM образов.
2. На мигрированной изолированной копии PostgreSQL выполнить регрессию и реальные
   параллельные операции: manual/normal create, accept, close, amount/file
   mutation, блокировку контрагента. Новых миграций в этом diff нет, но наличие
   прежних миграций и фактическую схему целевой БД нужно проверить.
3. Запустить read-only `check-iam.*` и live `smoke-infra.*` на целевом стенде.
   Разобрать RBAC drift, orphan/missing accounts и inactive bindings; проверка
   сама больше ничего не исправляет. Проверить gateway/TLS/internal ports.
4. Пройти подготовленными тестовыми accounts E2E: no-mail создание/вход/пароли,
   CSRF, обновление grants/роли, чужой unit scope, чат, expiry/refresh/reconnect,
   файлы и desktop/mobile/keyboard/error/loading состояния затронутых форм.
   В текущей сессии реальные браузерные сценарии и визуальная проверка не выполнялись.
5. Проверить рабочие SMTP/IMAP/RabbitMQ/MinIO/ClamAV связи и доставку уведомлений
   в обоих email modes. Новая live-проверка чата добавляет IAM RPC перед
   командами/рассылкой: измерить задержку и нагрузку при ожидаемом числе участников.
6. Зафиксировать решение по остаточным advisory и проверить процедуру rollback.

Дополнительные границы: in-memory WS tickets/rate limiters имеют process-local
область; при нескольких workers нужны проверка маршрутизации и ограничения
нагрузки. `asyncio.wait_for(to_thread(...))` file guard прекращает ожидание,
но не убивает уже исполняющийся parser thread; hard resource isolation требует
отдельной проверки нагрузкой. After-commit notification hooks сохраняют
best-effort семантику: падение доставки после commit не откатывает бизнес-запись.
Эти свойства выявлены чтением кода; эксплуатация нагрузкой и потеря сообщений
в этой сессии не воспроизводились.

## Артефакты

Локальные логи и JSON находятся в игнорируемом `artifacts/refactor-audit/`:
`backend-unit-final.log`, `backend-integration-final.log`, `iam-final.log`,
`file-guard-final.log`, `frontend-unit-final.log`, `frontend-lint-final.log`,
`frontend-build-final.log`, `npm-audit-final.json`, `npm-production-audit.json`,
`python-manifest-audit-final.json`, `python-installed-audit-final.json`.
Промежуточные логи сохраняют исходные падения и ход обновления зависимостей.

Результат относится к рабочему diff поверх `06567a4`; последующие изменения
потребуют соответствующей повторной проверки. Аудит исходников и тесты не
доказывают отсутствие всех возможных уязвимостей и не заменяют проверку стенда.
