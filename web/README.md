# Web AcomOfferDesk

React/Vite frontend является тонким клиентом backend API.

## Auth flow

- вход начинается переходом на `/api/v1/auth/login`;
- callback, refresh и logout обслуживает BFF;
- access/refresh tokens находятся в HttpOnly cookies;
- frontend не читает, не декодирует и не хранит JWT;
- `/api/v1/auth/session` возвращает роль, status и permissions для UI;
- окончательное решение о доступе всегда принимает backend.

## Команды

```powershell
npm --prefix web run lint
npm --prefix web run test:unit
npm --prefix web run build
```

Playwright smoke использует заранее подготовленные IAM credentials из `E2E_*_USERNAME`/`E2E_*_PASSWORD` и запускается через `scripts/e2e-smoke.ps1` или `scripts/e2e-smoke.sh`.
