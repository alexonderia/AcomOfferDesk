# Матрица permissions

Канонический список permission codes находится в `backend/app/domain/permissions.py`. IAM RBAC seed строится из этого контракта и системных role names из `backend/app/domain/iam_roles.py`.

## Правила

- IAM хранит role permissions и `account_permission_grants`.
- Effective permissions равны union permissions роли и индивидуальных grants.
- Access token содержит только известные application permission codes; неизвестное значение отклоняет token целиком.
- `users.id_role` не создаёт permissions и не является fallback.
- `CurrentUser.role_id` приходит из проверенного IAM system role и может использоваться domain policies как тип участника процесса.
- Unit hierarchy и memberships ограничивают data scope независимо от functional permission.
- Frontend permissions/actions служат для UX; enforcement остаётся на backend.

## Registration lifecycle

- `users.registration.invite` — выпуск HMAC-подписанного stateless registration invite (MAIN invitation не хранит); contractor batch invite также допускает `contractors.manual.create`.
- `users.registration.approve` — единственный переход саморегистрации `review → active` при verified primary email (superadmin/admin/security).

## Individual access

Базовое чтение workspace КП у ВЭ/Э ограничено своим подразделением и потомками; расширение до корня требует соответствующего делегирования. Право просмотра не даёт изменения суммы/файлов КП. При рассылке чата существующая WebSocket-подписка повторно проверяется по текущему бизнес-статусу, активной IAM-привязке, актуальным permissions и области чата. Отзыв членства или grant закрывает доставку новых сообщений на открытом соединении.

`normative_files.read` разрешает скачать норматив без общего `files.download`; файлы заявок и КП это исключение не открывает. Сообщения чата во всех каналах ограничены 3000 символами после удаления внешних пробелов.

Смена собственного пароля требует active и проверки текущего пароля, account/session берутся из авторизации. В собственном профиле `actions.can_manage_credentials=true` при active. Создание с паролем при отключённой почте сохраняет существующие permissions, допустимые роли и unit scope. Преобразование сотрудник/контрагент доступно только СА при отсутствии несовместимых связей.

Department и contractor delegation UI сохраняют изменения только в IAM grants. UI access codes могут оставаться стабильными identifiers, но runtime authorization проверяет соответствующие atomic permission codes. Удаление индивидуального grant не снимает permission, если он наследуется от system role.

## Изменение матрицы

При добавлении или удалении permission необходимо синхронно обновить:

1. `PermissionCodes` и role matrix в backend;
2. IAM seed/report tests;
3. backend policies/actions;
4. frontend guards и tests;
5. этот документ и coverage map.
