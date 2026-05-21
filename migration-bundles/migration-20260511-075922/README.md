# Migration Bundle 20260511-075922

This bundle contains a pre-clean snapshot of `order_database` and Keycloak realm data.

## Contents

- `order_database_data.sql` - data-only SQL export from PostgreSQL
- `order_database_full.dump` - full PostgreSQL dump (`pg_dump -Fc`)
- `keycloak_users.json` - Keycloak users snapshot before cleanup
- `keycloak_roles.json` - Keycloak roles snapshot
- `keycloak_groups.json` - Keycloak groups snapshot
- `restore_migration_bundle.sh` - helper restore script
- `SHA256SUMS.txt` - checksums for integrity verification

## Where this was created

- Source VPS path: `/opt/order_database/backups/migration-20260511-075922`
- Local copy path: `migration-bundles/migration-20260511-075922`

## Quick usage

Run on a host that has Docker Compose access to `/opt/order_database`:

```bash
cd migration-bundles/migration-20260511-075922
./restore_migration_bundle.sh verify
./restore_migration_bundle.sh db-sql
```

Alternative full restore:

```bash
cd migration-bundles/migration-20260511-075922
./restore_migration_bundle.sh db-dump
```

## Notes

- `db-sql` expects existing schema (Flyway/init already applied).
- `db-dump` recreates `order_database` and restores from full dump.
- `keycloak_users.json` is preserved for manual filtering/import planning in the new contour.
