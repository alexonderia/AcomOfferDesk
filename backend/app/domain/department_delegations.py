from __future__ import annotations

from dataclasses import dataclass


DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE: dict[str, str] = {
    "department.requests.read": "delegation.department.requests.read",
    "department.requests.update": "delegation.department.requests.update",
    "department.requests.status_update": "delegation.department.requests.status_update",
    "department.requests.assign": "delegation.department.requests.assign",
    "department.offers.update": "delegation.department.offers.update",
    "department.offers.accept": "delegation.department.offers.accept",
    "department.offers.reject": "delegation.department.offers.reject",
    "department.chats.read": "delegation.department.chats.read",
    "department.chats.send_message": "delegation.department.chats.send_message",
    "department.files.read": "delegation.department.files.read",
    "department.files.upload": "delegation.department.files.upload",
    "department.files.delete": "delegation.department.files.delete",
    "department.dashboard.read": "delegation.department.dashboard.read",
    "department.plans.read": "delegation.department.plans.read",
    "department.plans.manage": "delegation.department.plans.manage",
}

DEPARTMENT_DELEGATION_ROLE_TO_PERMISSION: dict[str, str] = {
    role_code: permission_code
    for permission_code, role_code in DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE.items()
}


@dataclass(frozen=True, slots=True)
class DepartmentDelegationDefinition:
    role_code: str
    permission_code: str
    label: str
    group: str


DEPARTMENT_DELEGATIONS: tuple[DepartmentDelegationDefinition, ...] = (
    DepartmentDelegationDefinition(
        role_code="delegation.department.requests.read",
        permission_code="department.requests.read",
        label="Просмотр заявок подразделения",
        group="requests",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.requests.update",
        permission_code="department.requests.update",
        label="Редактирование заявок подразделения",
        group="requests",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.requests.status_update",
        permission_code="department.requests.status_update",
        label="Изменение статусов заявок",
        group="requests",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.requests.assign",
        permission_code="department.requests.assign",
        label="Назначение ответственного",
        group="requests",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.offers.update",
        permission_code="department.offers.update",
        label="Изменение КП (сумма и файлы)",
        group="offers",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.offers.accept",
        permission_code="department.offers.accept",
        label="Принятие КП",
        group="offers",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.offers.reject",
        permission_code="department.offers.reject",
        label="Отклонение КП",
        group="offers",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.chats.read",
        permission_code="department.chats.read",
        label="Просмотр чатов подразделения",
        group="chats",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.chats.send_message",
        permission_code="department.chats.send_message",
        label="Отправка сообщений в чатах подразделения",
        group="chats",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.files.read",
        permission_code="department.files.read",
        label="Просмотр файлов подразделения",
        group="files",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.files.upload",
        permission_code="department.files.upload",
        label="Загрузка файлов подразделения",
        group="files",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.files.delete",
        permission_code="department.files.delete",
        label="Удаление файлов подразделения",
        group="files",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.dashboard.read",
        permission_code="department.dashboard.read",
        label="Просмотр статистики подразделения",
        group="dashboard",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.plans.read",
        permission_code="department.plans.read",
        label="Просмотр планов подразделения",
        group="plans",
    ),
    DepartmentDelegationDefinition(
        role_code="delegation.department.plans.manage",
        permission_code="department.plans.manage",
        label="Управление планами подразделения",
        group="plans",
    ),
)


def get_department_delegation_role_codes() -> frozenset[str]:
    return frozenset(DEPARTMENT_DELEGATION_ROLE_TO_PERMISSION.keys())


def get_department_permission_codes() -> frozenset[str]:
    return frozenset(DEPARTMENT_PERMISSION_TO_DELEGATION_ROLE.keys())
