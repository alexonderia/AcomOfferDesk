import asyncio

import app.api.dependencies as api_dependencies
from app.api.dependencies import build_current_user_from_keycloak_claims, require_permission
from app.core.config import settings
from app.domain.auth_context import build_current_user_from_keycloak
from app.domain.exceptions import Forbidden
from app.domain.permissions import PermissionCodes
from app.services import keycloak_oidc


def _run(coroutine):
    return asyncio.run(coroutine)


def test_decode_keycloak_access_token_extracts_api_roles_from_resource_access(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_api_client_id", "acom-api")

    issuer = settings.resolved_keycloak_issuer_url

    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_header", lambda _: {"kid": "kid-1", "alg": "RS256"})
    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_claims", lambda _: {"iss": issuer})

    async def fake_get_jwks():
        return {"keys": [{"kid": "kid-1"}]}

    monkeypatch.setattr(keycloak_oidc, "_get_jwks", fake_get_jwks)
    monkeypatch.setattr(
        keycloak_oidc.jwt,
        "decode",
        lambda *_args, **_kwargs: {
            "iss": issuer,
            "sub": "user-1",
            "iat": 100,
            "exp": 200,
            "aud": [settings.keycloak_client_id],
            "resource_access": {
                "acom-api": {
                    "roles": [
                        PermissionCodes.USERS_READ,
                        "app.admin",
                        "delegation.user-manager",
                        " ",
                    ]
                }
            },
        },
    )

    claims = _run(keycloak_oidc.decode_keycloak_access_token("token"))

    assert claims.api_roles == frozenset(
        {
            PermissionCodes.USERS_READ,
            "app.admin",
            "delegation.user-manager",
        }
    )


def test_decode_keycloak_access_token_handles_missing_resource_access(monkeypatch):
    issuer = settings.resolved_keycloak_issuer_url

    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_header", lambda _: {"kid": "kid-1", "alg": "RS256"})
    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_claims", lambda _: {"iss": issuer})

    async def fake_get_jwks():
        return {"keys": [{"kid": "kid-1"}]}

    monkeypatch.setattr(keycloak_oidc, "_get_jwks", fake_get_jwks)
    monkeypatch.setattr(
        keycloak_oidc.jwt,
        "decode",
        lambda *_args, **_kwargs: {
            "iss": issuer,
            "sub": "user-1",
            "iat": 100,
            "exp": 200,
            "aud": [settings.keycloak_client_id],
        },
    )

    claims = _run(keycloak_oidc.decode_keycloak_access_token("token"))

    assert claims.api_roles == frozenset()


def test_decode_keycloak_access_token_returns_empty_roles_when_api_client_mismatch(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_api_client_id", "acom-api")
    issuer = settings.resolved_keycloak_issuer_url

    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_header", lambda _: {"kid": "kid-1", "alg": "RS256"})
    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_claims", lambda _: {"iss": issuer})

    async def fake_get_jwks():
        return {"keys": [{"kid": "kid-1"}]}

    monkeypatch.setattr(keycloak_oidc, "_get_jwks", fake_get_jwks)
    monkeypatch.setattr(
        keycloak_oidc.jwt,
        "decode",
        lambda *_args, **_kwargs: {
            "iss": issuer,
            "sub": "user-1",
            "iat": 100,
            "exp": 200,
            "aud": [settings.keycloak_client_id],
            "resource_access": {
                "another-api-client": {
                    "roles": [PermissionCodes.USERS_READ],
                }
            },
        },
    )

    claims = _run(keycloak_oidc.decode_keycloak_access_token("token"))

    assert claims.api_roles == frozenset()


def test_decode_keycloak_access_token_extracts_roles_from_authorization_permissions(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_api_client_id", "acom-api")
    issuer = settings.resolved_keycloak_issuer_url

    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_header", lambda _: {"kid": "kid-1", "alg": "RS256"})
    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_claims", lambda _: {"iss": issuer})

    async def fake_get_jwks():
        return {"keys": [{"kid": "kid-1"}]}

    monkeypatch.setattr(keycloak_oidc, "_get_jwks", fake_get_jwks)
    monkeypatch.setattr(
        keycloak_oidc.jwt,
        "decode",
        lambda *_args, **_kwargs: {
            "iss": issuer,
            "sub": "user-1",
            "iat": 100,
            "exp": 200,
            "aud": [settings.keycloak_client_id],
            "authorization": {
                "permissions": [
                    {"scopes": [PermissionCodes.CHAT_READ, " "]},
                    {"permissions": [PermissionCodes.CHAT_MESSAGE_SEND]},
                ]
            },
        },
    )

    claims = _run(keycloak_oidc.decode_keycloak_access_token("token"))

    assert claims.api_roles == frozenset({PermissionCodes.CHAT_READ, PermissionCodes.CHAT_MESSAGE_SEND})


def test_decode_keycloak_access_token_extracts_roles_from_top_level_permissions(monkeypatch):
    monkeypatch.setattr(settings, "keycloak_api_client_id", "acom-api")
    issuer = settings.resolved_keycloak_issuer_url

    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_header", lambda _: {"kid": "kid-1", "alg": "RS256"})
    monkeypatch.setattr(keycloak_oidc.jwt, "get_unverified_claims", lambda _: {"iss": issuer})

    async def fake_get_jwks():
        return {"keys": [{"kid": "kid-1"}]}

    monkeypatch.setattr(keycloak_oidc, "_get_jwks", fake_get_jwks)
    monkeypatch.setattr(
        keycloak_oidc.jwt,
        "decode",
        lambda *_args, **_kwargs: {
            "iss": issuer,
            "sub": "user-1",
            "iat": 100,
            "exp": 200,
            "aud": [settings.keycloak_client_id],
            "permissions": [
                {"name": PermissionCodes.REQUESTS_READ},
                {"permission": PermissionCodes.REQUESTS_UPDATE},
            ],
        },
    )

    claims = _run(keycloak_oidc.decode_keycloak_access_token("token"))

    assert claims.api_roles == frozenset({PermissionCodes.REQUESTS_READ, PermissionCodes.REQUESTS_UPDATE})


def test_build_current_user_from_keycloak_filters_known_permissions():
    current_user = build_current_user_from_keycloak(
        user_id="user-1",
        role_id=2,
        status="active",
        api_roles=frozenset(
            {
                PermissionCodes.USERS_READ,
                "unknown.permission",
                "app.admin",
                "delegation.user-manager",
            }
        ),
    )

    assert current_user.permissions == frozenset({PermissionCodes.USERS_READ})


def test_build_current_user_from_keycloak_splits_app_and_delegation_roles():
    current_user = build_current_user_from_keycloak(
        user_id="user-1",
        role_id=2,
        status="active",
        api_roles=frozenset(
            {
                "app.economist",
                "delegation.request-deleter",
                PermissionCodes.REQUESTS_READ,
            }
        ),
    )

    assert current_user.app_roles == frozenset({"app.economist"})
    assert current_user.delegation_roles == frozenset({"delegation.request-deleter"})
    assert "app.economist" not in current_user.permissions
    assert "delegation.request-deleter" not in current_user.permissions


def test_require_permission_denies_when_permission_missing():
    dependency = require_permission(PermissionCodes.USERS_READ)
    current_user = build_current_user_from_keycloak(
        user_id="user-1",
        role_id=2,
        status="active",
        api_roles=frozenset(),
    )

    try:
        _run(dependency(current_user=current_user))
    except Forbidden:
        pass
    else:
        raise AssertionError("Expected Forbidden")


def test_require_permission_denies_non_active_statuses():
    dependency = require_permission(PermissionCodes.USERS_READ)

    for status in ("review", "inactive", "blacklist"):
        current_user = build_current_user_from_keycloak(
            user_id="user-1",
            role_id=2,
            status=status,
            api_roles=frozenset({PermissionCodes.USERS_READ}),
        )
        try:
            _run(dependency(current_user=current_user))
        except Forbidden:
            continue
        raise AssertionError(f"Expected Forbidden for status={status}")


def test_require_permission_dependency_uses_domain_authorization(monkeypatch):
    dependency = require_permission(PermissionCodes.USERS_READ)
    current_user = build_current_user_from_keycloak(
        user_id="user-1",
        role_id=settings.admin_role_id,
        status="active",
        api_roles=frozenset({PermissionCodes.USERS_READ}),
    )

    captured: dict[str, str] = {}

    def fake_enforce_permission(user, permission_code):
        captured["user_id"] = user.user_id
        captured["permission_code"] = permission_code

    monkeypatch.setattr(api_dependencies, "enforce_permission", fake_enforce_permission)

    resolved = _run(dependency(current_user=current_user))

    assert resolved is current_user
    assert captured == {"user_id": "user-1", "permission_code": PermissionCodes.USERS_READ}


def test_build_current_user_from_keycloak_claims_takes_permissions_from_token_claims():
    current_user = build_current_user_from_keycloak_claims(
        user_id="user-1",
        role_id=settings.admin_role_id,
        status="active",
        keycloak_api_roles=frozenset(
            {
                PermissionCodes.REQUESTS_READ,
                "app.admin",
            }
        ),
    )

    assert current_user.permissions == frozenset({PermissionCodes.REQUESTS_READ})
    assert current_user.app_roles == frozenset({"app.admin"})
