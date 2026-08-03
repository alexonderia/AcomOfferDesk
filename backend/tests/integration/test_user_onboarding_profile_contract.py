from __future__ import annotations

from types import SimpleNamespace

from app.core.config import settings


class _OnboardingProfilesRepo:
    def __init__(self, profile=None) -> None:
        self.profile = profile

    async def get_by_id(self, user_id: str):
        _ = user_id
        return self.profile

    async def add(self, profile) -> None:
        self.profile = profile


class _OnboardingCompanyContactsRepo:
    def __init__(self, company_contact=None) -> None:
        self.company_contact = company_contact

    async def get_by_id(self, user_id: str):
        _ = user_id
        return self.company_contact

    async def add(self, company_contact) -> None:
        self.company_contact = company_contact


class _OnboardingUsersRepo:
    def __init__(self, *, profiles: _OnboardingProfilesRepo, company_contacts: _OnboardingCompanyContactsRepo) -> None:
        self._profiles = profiles
        self._company_contacts = company_contacts
        self._user = SimpleNamespace(
            id="contractor-review-1",
            id_role=settings.contractor_role_id,
            status="review",
        )

    async def get_with_profile_and_company_contacts(self, *, user_id: str):
        _ = user_id
        return self._user, self._profiles.profile, self._company_contacts.company_contact


class _OnboardingPeriodsRepo:
    async def get_active_for_user(self, *, user_id: str):
        _ = user_id
        return None

    async def list_for_user(self, *, user_id: str):
        _ = user_id
        return []


class _OnboardingUserAuthAccountsRepo:
    async def get_by_user_provider(self, *, user_id: str, provider: str, include_inactive: bool = False):
        _ = (user_id, provider, include_inactive)
        return None


class _OnboardingUow:
    def __init__(self, *, profile=None, company_contact=None) -> None:
        self.profiles = _OnboardingProfilesRepo(profile)
        self.company_contacts = _OnboardingCompanyContactsRepo(company_contact)
        self.users = _OnboardingUsersRepo(
            profiles=self.profiles,
            company_contacts=self.company_contacts,
        )
        self.user_status_periods = _OnboardingPeriodsRepo()
        self.user_auth_accounts = _OnboardingUserAuthAccountsRepo()

    async def __aenter__(self) -> "_OnboardingUow":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)


def test_review_contractor_without_profile_permission_is_still_blocked_on_regular_me_endpoint(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(
        make_current_user(
            user_id="contractor-review-1",
            role_id=settings.contractor_role_id,
            status="review",
            permissions=set(),
        )
    )
    set_uow(_OnboardingUow())

    response = test_client.get("/api/v1/users/me")

    assert response.status_code == 403


def test_review_contractor_without_profile_permission_can_read_registration_onboarding_profile(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(
        make_current_user(
            user_id="contractor-review-1",
            role_id=settings.contractor_role_id,
            status="review",
            permissions=set(),
        )
    )
    set_uow(
        _OnboardingUow(
            profile=SimpleNamespace(full_name="Иван Иванов", phone="+79991234567", mail="ivan@example.com"),
            company_contact=SimpleNamespace(
                company_name='ООО "Тест"',
                inn="7707083893",
                phone="+79990000000",
                mail="company@example.com",
                address="Москва",
                note="Комментарий",
            ),
        )
    )

    response = test_client.get("/api/v1/users/me/registration-profile")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["full_name"] == "Иван Иванов"
    assert payload["company_name"] == 'ООО "Тест"'
    assert payload["actions"]["can_manage_own_profile"] is True
    assert payload["actions"]["can_manage_company_contacts"] is True


def test_review_contractor_without_profile_permission_can_update_registration_onboarding_profile(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(
        make_current_user(
            user_id="contractor-review-1",
            role_id=settings.contractor_role_id,
            status="review",
            permissions=set(),
        )
    )
    set_uow(_OnboardingUow())

    response = test_client.patch(
        "/api/v1/users/me/registration-profile",
        json={
            "full_name": "Петров Петр",
            "phone": "+79995554433",
            "mail": "petrov@example.com",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["full_name"] == "Петров Петр"
    assert payload["phone"] == "+79995554433"
    assert payload["mail"] == "petrov@example.com"
    assert payload["actions"]["can_manage_own_profile"] is True


def test_review_contractor_without_company_permission_can_update_registration_company_contacts(
    test_client,
    set_current_user,
    set_uow,
    make_current_user,
):
    set_current_user(
        make_current_user(
            user_id="contractor-review-1",
            role_id=settings.contractor_role_id,
            status="review",
            permissions=set(),
        )
    )
    set_uow(_OnboardingUow())

    response = test_client.patch(
        "/api/v1/users/me/registration-company-contacts",
        json={
            "company_name": 'ООО "Ромашка"',
            "inn": "7707083893",
            "company_phone": "+79990000000",
            "company_mail": "company@example.com",
            "address": "Москва",
            "note": "Примечание",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["company_name"] == 'ООО "Ромашка"'
    assert payload["inn"] == "7707083893"
    assert payload["company_phone"] == "+79990000000"
    assert payload["company_mail"] == "company@example.com"
    assert payload["actions"]["can_manage_company_contacts"] is True
