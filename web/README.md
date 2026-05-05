# Web (`/web`)

## Граница ответственности документа

Этот README описывает frontend-модуль и навигацию по коду.
Единый источник правды по запуску окружений и compose-слоям:
- `docs/environments.md`

Статус локального compose в `/web`:
- `web/docker-compose.yml` — standalone/локальный вспомогательный сценарий, не основной путь запуска проекта.

Frontend-клиент AcomOfferDesk на `React + TypeScript`. Этот модуль отвечает за пользовательский интерфейс, маршрутизацию, формы, интеграцию с backend API и клиентскую часть auth/realtime-сценариев.

## Роль модуля в системе

`web` - это SPA, через которую работают:

- сотрудники;
- контрагенты;
- администраторы;
- пользователи dashboard и раздела управления.

Frontend не содержит основной бизнес-логики доступа. Он получает данные, permissions и action flags от backend и рендерит интерфейс на их основе.

## Что важно знать в первую очередь

- все API-вызовы идут по относительным путям `/api/...`;
- login построен через Keycloak redirect flow;
- восстановление сессии происходит через `POST /api/v1/auth/refresh`;
- доступ к экранам ограничивается как routing-guard'ами, так и данными, которые backend возвращает в `actions` и `permissions`;
- чат оффера использует realtime-подключение.

## Стек

- React 18
- TypeScript
- Vite
- MUI
- React Router
- React Hook Form
- Zod

## Структура `src`

```text
src/
  app/        каркас приложения, провайдеры, routes, layout
  pages/      route-level страницы
  features/   прикладные сценарии и крупные UI-блоки
  entities/   типы и представления доменных сущностей
  shared/     API-клиент, общие компоненты, utils, constants, theme, ws
```

## Как искать код по задачам

### Если нужно поменять страницу

Начинайте с `src/pages/`, затем переходите в соответствующую feature.

Типовые входы:

- `src/pages/auth/*`
- `src/pages/requests/*`
- `src/pages/offers/*`
- `src/pages/admin/*`
- `src/pages/dashboard/*`

### Если нужно поменять поведение экрана

Смотрите в `src/features/`.

Именно там обычно находятся:

- page hooks;
- form orchestration;
- составные карточки, панели и таблицы;
- прикладные вычисления и адаптация API-ответов к UI.

### Если нужно поменять API-вызов

Смотрите в `src/shared/api/`.

Это основной слой для:

- HTTP-запросов;
- маппинга ответов;
- формирования payload;
- разбиения API по доменным зонам.

### Если нужно поменять маршруты

Смотрите:

- `src/app/routes/AppRoutes.tsx`
- `src/app/routes/ProtectedRoute.tsx`
- `src/app/routes/RoleRoute.tsx`

## Ключевые зоны frontend

### `app/`

Каркас приложения.

Здесь расположены:

- корневой `App`;
- auth provider;
- chat realtime provider;
- route guards;
- layout.

Ключевые файлы:

- `src/app/App.tsx`
- `src/app/routes/AppRoutes.tsx`
- `src/app/providers/AuthProvider.tsx`
- `src/app/providers/ChatRealtimeProvider.tsx`

### `pages/`

Страницы как точки входа маршрутов. Это хороший старт, если вы знаете URL или пользовательский экран, который нужно изменить.

### `features/`

Слой прикладной логики интерфейса.

Особенно важные зоны:

- `features/requests`
- `features/request-details`
- `features/offer-workspace`
- `features/admin`
- `features/dashboard`
- `features/header`

### `shared/`

Общие части приложения:

- `shared/api`
- `shared/components`
- `shared/ui`
- `shared/ws`
- `shared/constants`
- `shared/theme`

## Маршрутизация и доступ

Фактические route-level входы определены в `src/app/routes/AppRoutes.tsx`.

Среди основных маршрутов:

- `/login`
- `/auth/callback`
- `/account`
- `/requests`
- `/requests/create`
- `/requests/:id`
- `/requests/:id/contractor`
- `/offers/:id/workspace`
- `/admin`
- `/feedback`
- `/pm-dashboard`

Ограничение доступа строится в несколько слоев:

1. Наличие сессии.
2. Route guards (`ProtectedRoute`, `RoleRoute`).
3. Backend-driven `actions` и `permissions`.

## Как frontend взаимодействует с backend

Основной поток выглядит так:

1. Страница или feature вызывает функцию из `shared/api`.
2. Backend возвращает данные и разрешенные действия.
3. Feature или page hook адаптирует результат для UI.
4. Компоненты отображают только доступные пользователю действия.

Это особенно важно в зонах:

- заявок;
- офферов;
- чата;
- управления пользователями.

## Auth во frontend

Frontend использует только Keycloak redirect flow.

Практически это означает:

- нет локальной формы password login, работающей независимо от Keycloak;
- frontend инициирует переход в auth flow;
- после callback сессия восстанавливается через refresh endpoint;
- часть логики onboarding зависит от статуса пользователя и возвращаемых backend-полей.

Смотрите:

- `src/app/providers/AuthProvider.tsx`
- `src/pages/auth/*`

## Realtime и чат

Чат оффера работает через отдельный realtime-слой.

На стороне frontend за это отвечают:

- `src/app/providers/ChatRealtimeProvider.tsx`
- `src/shared/ws/chatSocket.ts`
- `src/features/offer-workspace/*`

Через этот поток приходят:

- новые сообщения;
- статусы доставки;
- статусы прочтения.

## Запуск

### В составе основного проекта

Рекомендуемый способ:

```bash
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Точка входа:

- `http://localhost:8080`

### Отдельно как dev-server

```bash
cd web
npm install
npm run dev
```

По умолчанию Vite стартует на:

- `http://localhost:4173`

## Скрипты

Доступные команды из `package.json`:

- `npm run dev`
- `npm run build`
- `npm run preview`
- `npm run lint`

## Что читать дальше

- верхний уровень проекта: `README.md`
- общая архитектура: `docs/runtime-architecture.md`
- навигация по всей кодовой базе: `docs/developer-guide.md`
- аутентификация и онбординг: `docs/auth-and-onboarding.md`
- окружения и perimeter: `docs/environments.md`

