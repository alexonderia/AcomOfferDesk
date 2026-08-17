# Руководство разработчика

## Перед изменением

1. Найдите существующий route/service/repository/component.
2. Для access-control изменений проследите путь IAM token → `CurrentUser.permissions` → policy/service → response actions → frontend guard.
3. Не вычисляйте permissions из `users.id_role`.
4. Сохраняйте unit scope и domain policies в Acom.

## Backend

```powershell
$env:PYTHONPATH = (Resolve-Path backend).Path
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

## IAM

```powershell
$env:PYTHONPATH = (Resolve-Path iam).Path
.\.venv\Scripts\python.exe -m pytest iam/tests -q
```

## Frontend

```powershell
npm --prefix web run lint
npm --prefix web run test:unit
npm --prefix web run build
```

## Cross-layer auth rule

Frontend инициирует `/api/v1/auth/login`, получает session DTO и не работает с token payload. Backend локально валидирует IAM token, связывает identity только через IAM binding и использует token permissions. Individual access UI изменяет grants только через IAM.
