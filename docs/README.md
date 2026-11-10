# Документация AcomOfferDesk

Здесь находятся действующие инструкции и контракты. [Отчёты](reports/README.md) фиксируют состояние конкретной версии и окружения; [архив](archive/README.md) содержит предыдущие решения и выгрузки. Инструкции для агентов — [AGENTS.md](../AGENTS.md).

## Продукт и архитектура

- [Обзор приложения и границы ответственности](product/project-overview.md)
- [Runtime: сервисы, gateway и БД](product/runtime-architecture.md)

## Разработка и проверка

- [Руководство разработчика](development/developer-guide.md)
- [Backend: слои, данные, ошибки и логирование](development/backend-guidelines.md)
- [Frontend: компоненты, состояние, типы и UI](development/frontend-guidelines.md)
- [Жизненный цикл заявок и КП](development/request-offer-lifecycle.md)
- [Тестирование: команды, каталог, покрытие и smoke](development/testing-strategy.md)
- [Повторяемая ручная регрессия](qa/manual-regression.md)
- [Генерация пользовательских памяток из DOCX](development/role-guides.md)

## Доступ и файлы

- [IAM, BFF, регистрация, сессии и пароли](security/auth-and-onboarding.md)
- [Permissions, grants, unit scope и контрагенты](security/permissions-matrix.md)
- [Безопасность загрузки файлов](file-security.md)
- [Предпросмотр файлов](operations/file-preview.md)

## Эксплуатация

- [Окружения и compose](operations/environments.md)
- [Эксплуатация IAM и ротация ключей](iam/operations.md)
- [Backup и restore IAM](iam/backup-restore.md)
- [Миграция локальных тестовых IAM-аккаунтов](iam/local-account-migration.md)
- [Работа без почты и управление паролями](operations/no-mail-accounts.md)
- [Панель состояния системы](operations/system-status.md)
- [Матрица событий и получателей уведомлений](operations/notifications-matrix.md)
- [Технический контракт доставки уведомлений](development/notification-service.md)
- [Технические работы и fallback gateway](operations/maintenance.md)
- [Основная БД и Flyway на VPS](operations/order-database-vps.md)
- [VPS troubleshooting](operations/vps-troubleshooting.md)
- [Продвижение веток](operations/branch-merge-policy.md)
- [Production environment](release/production-env.md)
- [Release checklist](release/release-checklist.md)

## Правила обновления

Изменение поведения сопровождается правкой соответствующего тематического документа. Не копируйте целиком один контракт в разные документы: добавляйте ссылку.
Отчёты называются `YYYY-MM-DD-topic.ext`; в тексте указываются версия, окружение, реальные результаты и ограничения. Файлы debug/сборок помещаются в игнорируемый `artifacts/`.
Проверка локальных Markdown-ссылок: `python scripts/check_docs.py`.
