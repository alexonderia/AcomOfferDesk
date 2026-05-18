# Тесты backend

В этой директории собраны backend-тесты, разделенные по скорости выполнения и назначению.

## Структура

- `unit/`:
  быстрые изолированные тесты доменных правил и сборки `actions`;
  не требуют живых PostgreSQL/Keycloak/RabbitMQ/MinIO.
- `integration/`:
  проверки API-контрактов и авторизации через dependency override в FastAPI и контролируемые заглушки.
- `test_*.py` в корне:
  совместимость и миграционные guard-тесты, которые уже были в проекте.

## Подготовка окружения

Перед запуском тестов используйте отдельное виртуальное окружение.

PowerShell (Windows):
```powershell
cd C:\Users\alexonderia\Work\AcomOfferDesk
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -r backend\requirements.txt
pip install pytest pytest-asyncio
```

Bash (Linux/macOS/WSL):
```bash
cd /path/to/AcomOfferDesk
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio
```

Рекомендации:
- используйте Python `3.11` или `3.12` (предпочтительно `3.12`);
- для PowerShell запускайте `*.ps1`, для `*.sh` используйте `bash`;
- если видите `No module named pytest`, проверьте, что `.venv` активирован и зависимости установлены именно в него.

## Что покрывается

- Разбор ролей Keycloak в:
  `permissions`, `app_roles`, `delegation_roles`.
- Поведение `authorization.has_permission(...)` с учетом статуса:
  `active`, `review`, `inactive`, `blacklist`.
- Критичные решения политик:
  `RequestPolicy`, `OfferPolicy`, `UserPolicy`.
- Контракты backend-действий:
  `request`/`offer`/`chat`/`user actions`.
- Проверки API-контрактов:
  `actions` на уровне сущностей, отсутствие дублирования глобальных `permissions`, негативные сценарии `403`.

## Команды запуска

- Unit:
  - PowerShell: `./scripts/test-unit.ps1`
  - Bash: `./scripts/test-unit.sh`
- Integration:
  - PowerShell: `./scripts/test-integration.ps1`
  - Bash: `./scripts/test-integration.sh`

## Примечания

- Integration-тесты здесь проверяют именно контракты и намеренно легче, чем полноразмерные E2E на стенде.
- Браузерные E2E-проверки находятся отдельно в `web/e2e`.
- Для browser E2E можно использовать заранее подготовленные учетные данные или явный provisioning временных пользователей через `scripts/e2e-smoke.ps1 -ProvisionUsers`.
