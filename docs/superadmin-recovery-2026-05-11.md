# Superadmin Recovery (2026-05-11)

## Context

After cleanup of Keycloak users and `order_database` data, login through the app failed with:

`Не удалось завершить вход. Обратитесь к администратору, чтобы проверить доступ.`

Root cause was a sync gap:

- Keycloak user `superadmin` existed.
- Local DB user `users.id='superadmin'` and its `user_auth_accounts` binding were missing.

## Actions performed on VPS

1. Updated password for Keycloak user `superadmin` in realm `acom-offerdesk`.
2. Recreated local user in `order_database.users`:
   - `id='superadmin'`
   - `id_role=1` (superadmin)
   - `status='active'`
3. Recreated local-to-Keycloak binding in `user_auth_accounts` for provider `keycloak`.

## Verification

- `superadmin_local=1`
- `superadmin_keycloak_binding=1`
- User confirmed login as `superadmin` works in UI after recovery.

## Notes

- This is an operational recovery record; no credentials are stored in this file.
- Migration bundle for pre-clean state remains in `migration-bundles/migration-20260511-075922`.
