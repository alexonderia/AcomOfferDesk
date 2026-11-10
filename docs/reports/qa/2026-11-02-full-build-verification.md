# Полная пересборка Docker — 02.11.2026

**Блокировка снята. Все пять собираемых сервисов пересобраны из штатных Dockerfile с `--no-cache --pull` и запущены локально.**

## Что произошло с pip

Прежние попытки завершались `JSONDecodeError: Unterminated string` при чтении ответа индекса пакетов. При продолжении работы та же версия pip 25.0.1 в чистом `python:3.12-slim` успешно разрешила зависимости и скачала пакеты. Прямые проверки JSON индексов `pydantic-core`, `cryptography`, `greenlet` получили полные корректные ответы.

Ошибка больше не воспроизводится. Точный участок, на котором прежде обрезался ответ (сервер, промежуточный узел или транспорт), не локализован. Прежнее решение оставить эту ошибку блокирующей оказалось преждевременным.

## Выполнено

С общими локальными runtime env выполнены две команды:

```powershell
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml build --no-cache --pull backend iam web notifications_worker
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml build --no-cache --pull file_guard
```

Python-зависимости установлены заново штатным pip; web собран внутри Node-стадии Dockerfile через `npm install` и `npm run build`. Dockerfile и requirements менять не потребовалось.

| Сервис | Полная сборка | Проверка зависимостей | Работающий контейнер |
| --- | --- | --- | --- |
| backend | passed | `pip check` passed | новый образ, healthy |
| IAM | passed | `pip check` passed | новый образ, healthy |
| web | passed | TypeScript + Vite passed | новый образ, healthy |
| notifications_worker | passed | `pip check` passed | новый образ, healthy |
| file_guard | passed | `pip check` passed | новый образ, healthy |

Для всех пяти контейнеров проверено совпадение image ID с результатом свежей сборки. Временные образы поверх старых зависимостей больше не используются; локальный QA override также переключён на штатные теги.

## Проверка приложения

- **15 Playwright-тестов passed** одним прогоном: создание без email, смена пароля, заявки/КП/файлы, чат, feedback, планы, роли/статусы, границы подразделений и smoke/матрица семи ролей.
- Ещё **1 Playwright-тест passed** после переключения backend в почтовый режим: вход готового no-mail аккаунта, собственная смена пароля и запрет прямого административного создания с паролем. Затем восстановлен `EMAIL_ENABLED=false`. Внешняя доставка писем не выполнялась.
- Инфраструктурный smoke прошёл: gateway, health, IAM login/JWKS и изоляция internal API, PostgreSQL, MinIO, RabbitMQ.

Логи сборок, проверок и manifest image ID/версий пакетов сохранены в игнорируемом каталоге `artifacts/qa/20261102-full-build/`. Приложение работает на `http://localhost:8080` без почты. VPS не обновлялся.

Полная локальная сборка закрыта в [плане](../../archive/qa/2026-11-02-remediation-plan.md). В последующем [расширенном прогоне](2026-11-02-expanded-regression.md) исправлены дополнительные дефекты backend, который пересобран штатно поверх уже заново установленных зависимостей: 47/47 основных сценариев и ещё 4/4 no-mail E2E passed, backend 761 passed. Полный ручной перебор подпунктов DOCX и реальная почтовая доставка остаются отдельной приёмкой.
