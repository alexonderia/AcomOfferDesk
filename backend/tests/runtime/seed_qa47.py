"""Create a new, isolated QA47 dataset on a local no-mail stack.

Run inside backend with PYTHONPATH=/app. The output contains generated secrets;
keep it outside version control. This script only inserts new QA47 records.
"""

import argparse
import asyncio
import json
from pathlib import Path
import secrets

from app.core.config import settings
from app.core.uow import UnitOfWork
from app.domain.iam_identity import stable_iam_account_id
from app.domain.iam_roles import technical_role_name
from app.infrastructure.iam_client import IamClient
from app.models.auth_models import UserAuthAccount
from app.models.orm_models import CompanyContact, Profile, Unit, UnitMember, User


def make_inn() -> str:
    digits = "77" + "".join(str(secrets.randbelow(10)) for _ in range(7))
    check = sum(int(d) * w for d, w in zip(digits, [2, 4, 10, 3, 5, 9, 4, 6, 8])) % 11 % 10
    return digits + str(check)


async def seed(output: Path) -> None:
    if settings.email_enabled:
        raise RuntimeError("QA47 requires EMAIL_ENABLED=false")
    roles = {
        "SUPERADMIN": 1, "ADMIN": 2, "PROJECT_MANAGER": 4,
        "LEAD_ECONOMIST": 5, "ECONOMIST": 6, "OPERATOR": 7,
        "SUBORDINATE": 6, "PEER": 6, "FOREIGN": 6, "SPARE": 6,
        "CONTRACTOR": 3, "HIDDEN": 3, "INACTIVE": 3,
        "FOREIGN_CONTRACTOR": 3, "REVIEW_VERIFIED": 3,
        "REVIEW_UNVERIFIED": 3, "FOREIGN_MANAGER": 4, "ORDINARY": 3,
    }
    batch = "qa47_" + secrets.token_hex(4)
    data = {
        "batch": batch,
        "users": {
            label: {
                "login": batch + "_" + label.lower(),
                "password": secrets.token_urlsafe(24) + "Aa1!",
                "full_name": "QA47 " + batch + " " + label,
                "role_id": role, "inn": make_inn(),
            }
            for label, role in roles.items()
        },
        "units": {},
    }
    # Persist credentials before external IAM provisioning, also on partial failure.
    with output.open("x", encoding="utf-8") as handle:
        output.chmod(0o600)
        json.dump(data, handle)
    client = IamClient()
    async with UnitOfWork() as uow:
        for label, item in data["users"].items():
            login = item["login"]
            if await uow.users.get_by_id(login) is not None:
                raise RuntimeError("Refusing to overwrite an existing user")
            status = "review" if label.startswith("REVIEW_") else "inactive" if label == "INACTIVE" else "active"
            user = User(id=login, id_role=item["role_id"], status=status)
            await uow.users.add(user)
            await uow.session.flush([user])
            mail = login + "@example.invalid" if label.startswith("REVIEW_") else "Не указано"
            await uow.profiles.add(Profile(id=login, full_name=item["full_name"], phone="+79991234567", mail=mail))
            if item["role_id"] == 3:
                await uow.company_contacts.add(CompanyContact(id=login, company_name="QA47 " + label, inn=item["inn"], phone="+79991234567", mail="Не указано", address="QA47 fixture", note=batch))
            account = await client.provision_direct_credentials(account_id=stable_iam_account_id(login), login=login, role=technical_role_name(item["role_id"]), password=item["password"])
            auth_status = "pending" if status == "review" else "blocked" if status == "inactive" else "active"
            if account.auth_status != auth_status:
                await client.update_status(account_id=str(account.id), auth_status=auth_status, actor_account_id=None, actor_session_id=None)
            await uow.user_auth_accounts.add(UserAuthAccount(id_user=login, provider="iam", external_subject_id=str(account.id), external_username=login, is_active=True))
            if label == "ORDINARY":
                # Historical numeric messenger identity, used only as a fixture
                # to exercise the registered/manual-contractor distinction.
                await uow.user_auth_accounts.add(UserAuthAccount(id_user=login, provider="telegram", external_subject_id=str(8_000_000_000 + secrets.randbelow(1_000_000_000)), is_active=True))
            if label.startswith("REVIEW_"):
                await uow.user_contact_channels.upsert_channel(user_id=login, channel_type="email", channel_value=mail, is_verified=label == "REVIEW_VERIFIED", is_primary=True)
        await uow.session.flush()
        units = data["units"]
        for key, parent in [("A", None), ("B", None), ("A1", "A"), ("A11", "A1"), ("A2", "A")]:
            unit = Unit(name="QA47 " + batch + " " + key, id_parent=units.get(parent), id_created_by_user=data["users"]["SUPERADMIN"]["login"])
            uow.session.add(unit)
            await uow.session.flush()
            units[key] = unit.id
        memberships = {
            "SUPERADMIN": "A", "ADMIN": "A", "PROJECT_MANAGER": "A",
            "LEAD_ECONOMIST": "A1", "ECONOMIST": "A1", "OPERATOR": "A1",
            "SUBORDINATE": "A11", "PEER": "A2", "FOREIGN": "B",
            "CONTRACTOR": "A", "HIDDEN": "A", "INACTIVE": "A",
            "FOREIGN_CONTRACTOR": "B", "REVIEW_VERIFIED": "A",
            "REVIEW_UNVERIFIED": "A", "FOREIGN_MANAGER": "B", "ORDINARY": "A",
        }
        for label, key in memberships.items():
            uow.session.add(UnitMember(id_unit=units[key], id_user=data["users"][label]["login"], id_assigned_by_user=data["users"]["SUPERADMIN"]["login"], is_active=True))
    output.write_text(json.dumps(data), encoding="utf-8")
    print(json.dumps({"batch": batch, "users_created": len(roles), "units_created": len(units)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    asyncio.run(seed(parser.parse_args().output))
