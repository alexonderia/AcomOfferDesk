# AcomOfferDesk Keycloak Theme

Кастомная тема лежит здесь, чтобы жить рядом с realm import и bootstrap-логикой.

Что важно:

- Тема монтируется в контейнер Keycloak через корневой `docker-compose.yml`.
- Realm получает `loginTheme=acom-offerdesk` и через import, и через `infra/keycloak/bootstrap.sh`, поэтому настройка не теряется при уже существующем `keycloak_data`.
- Версия CSS/JS/картинок темы генерируется автоматически при старте контейнера `keycloak` через `infra/keycloak/prepare-theme.sh`, поэтому ручной `?v=...` bump больше не нужен.
- Тема адаптирована под текущий web-flow проекта:
  - вход для существующих сотрудников и связанных пользователей;
  - self-registration только для контрагентов;
  - после регистрации contractor получает локальный статус `review`.

Если нужно доработать UX дальше, основная точка входа:

- `login/template.ftl` — общий layout;
- `login/login.ftl` — вход;
- `login/register.ftl` — contractor registration;
- `resources/css/acom-offerdesk.css` — визуальные токены и стили;
- `messages/messages.properties` — словарь базовых подписей.
