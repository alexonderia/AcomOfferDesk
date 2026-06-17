from app.services.identity_sync import _normalize_full_name
from app.services.keycloak_oidc import KeycloakAccessTokenClaims


def _build_claims(**overrides) -> KeycloakAccessTokenClaims:
    payload = {
        "subject": "kc-subject",
        "issuer": "https://issuer.example.com/realms/acom-offerdesk",
        "issued_at": 1700000000,
        "expires_at": 1700003600,
        "preferred_username": "user",
        "full_name": "User Name",
        "given_name": "User",
        "family_name": "Name",
        "middle_name": None,
        "email": "user@example.com",
        "email_verified": True,
        "realm_roles": frozenset(),
        "api_roles": frozenset(),
    }
    payload.update(overrides)
    return KeycloakAccessTokenClaims(**payload)


def test_normalize_full_name_uses_middle_name_for_fio_order() -> None:
    claims = _build_claims(
        full_name="Иван Иванов",
        given_name="Иван",
        family_name="Иванов",
        middle_name="Иванович",
    )

    assert _normalize_full_name(claims) == "Иванов Иван Иванович"


def test_normalize_full_name_uses_fio_order_without_middle_name() -> None:
    claims = _build_claims(
        full_name="User Name",
        given_name="Имя",
        family_name="Фамилия",
        middle_name=None,
    )

    assert _normalize_full_name(claims) == "Фамилия Имя"


def test_normalize_full_name_uses_explicit_value_only_when_structured_parts_missing() -> None:
    claims = _build_claims(
        full_name="User Name",
        given_name=None,
        family_name=None,
        middle_name=None,
    )

    assert _normalize_full_name(claims) == "User Name"
