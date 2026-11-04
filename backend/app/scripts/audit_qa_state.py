"""Report QA identity/storage inconsistencies; repairs require an explicit user list."""
from __future__ import annotations

import argparse
import asyncio
import json

from app.core.uow import UnitOfWork
from app.domain.exceptions import NotFound
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.services.files import FileService
from app.services.iam_bindings import recover_existing_iam_binding


async def run(*, user_ids: list[str], check_iam: bool, check_storage: bool, repair_bindings: bool) -> dict:
    if repair_bindings and not user_ids:
        raise ValueError('Binding repair requires explicit --user arguments')
    report = {'users': [], 'normative_files': [], 'repairs': []}
    async with UnitOfWork() as uow:
        rows = await uow.users.list_all_with_profiles()
        bindings = await uow.user_auth_accounts.list_for_provider(provider='iam')
        by_user = {}
        for binding in bindings:
            by_user.setdefault(binding.id_user, []).append(binding)
        for user, _profile in rows:
            if user_ids and user.id not in user_ids:
                continue
            active = [b for b in by_user.get(user.id, []) if b.is_active]
            item = {'user_id': user.id, 'status': user.status, 'role': technical_role_name(user.id_role), 'active_iam_bindings': len(active)}
            if check_iam and active:
                try:
                    state = await IamClient().get_credential_state(account_id=active[0].external_subject_id)
                    item.update(login_matches=state.login == user.id, role_matches=state.role == item['role'], auth_status=state.auth_status, password_set=state.password_set)
                except Exception as exc:
                    item['iam_error'] = type(exc).__name__
            report['users'].append(item)
        if check_storage:
            files = FileService(uow.files)
            for normative in await uow.files.list_normative_files(status='actual'):
                item = {'normative_id': normative.id}
                try:
                    file = await uow.files.get_normative_file(normative_id=normative.id)
                    if file is None:
                        raise NotFound('metadata missing')
                    await files.ensure_content_available(db_file=file)
                    item['content_available'] = True
                except NotFound:
                    item['content_available'] = False
                except Exception as exc:
                    item['storage_error'] = type(exc).__name__
                report['normative_files'].append(item)
    if repair_bindings:
        for user_id in sorted(set(user_ids)):
            item = {'user_id': user_id}
            try:
                async with UnitOfWork() as uow:
                    user = await uow.users.get_by_id(user_id)
                    if user is None:
                        raise NotFound('user missing')
                    await recover_existing_iam_binding(uow, user_id=user_id)
                item['binding_recovered'] = True
            except Exception as exc:
                item['repair_error'] = type(exc).__name__
            report['repairs'].append(item)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user', action='append', default=[], dest='user_ids')
    parser.add_argument('--check-iam', action='store_true')
    parser.add_argument('--check-storage', action='store_true')
    parser.add_argument('--repair-bindings', action='store_true')
    args = parser.parse_args()
    if args.repair_bindings and not args.user_ids:
        parser.error('--repair-bindings requires at least one --user')
    try:
        report = asyncio.run(run(**vars(args)))
    except Exception as exc:
        print(json.dumps({'audit_error': type(exc).__name__}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if any('repair_error' in item for item in report['repairs']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
