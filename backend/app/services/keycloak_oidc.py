from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from jose import JWTError, jwt

from app.core.config import settings
from app.domain.exceptions import Forbidden, Unauthorized


@dataclass(frozen=True, slots=True)
class KeycloakTokenBundle:
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    id_token: str | None = None


@dataclass(frozen=True, slots=True)
class KeycloakAccessTokenClaims:
    subject: str
    issuer: str
    issued_at: int
    expires_at: int
    preferred_username: str | None
    full_name: str | None
    given_name: str | None
    family_name: str | None
    email: str | None
    email_verified: bool
    realm_roles: frozenset[str]


_jwks_cache: dict[str, Any] = {"keys": None, "fetched_at": 0.0}


async def _post_form(data: dict[str, str]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=settings.keycloak_http_timeout_seconds) as client:
        response = await client.post(
            settings.keycloak_token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code >= 400:
        raise Unauthorized("Keycloak token exchange failed")
    payload = response.json()
    if not isinstance(payload, dict):
        raise Unauthorized("Keycloak token exchange failed")
    return payload


async def exchange_code_for_tokens(*, code: str, code_verifier: str, redirect_uri: str | None = None) -> KeycloakTokenBundle:
    resolved_redirect_uri = (redirect_uri or settings.keycloak_callback_url).strip() or settings.keycloak_callback_url
    payload = await _post_form(
        {
            "grant_type": "authorization_code",
            "client_id": settings.keycloak_client_id,
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": resolved_redirect_uri,
        }
    )
    return KeycloakTokenBundle(
        access_token=str(payload.get("access_token") or ""),
        refresh_token=str(payload.get("refresh_token") or ""),
        expires_in=int(payload.get("expires_in") or 0),
        refresh_expires_in=int(payload.get("refresh_expires_in") or 0),
        id_token=str(payload.get("id_token") or "") or None,
    )


async def refresh_tokens(*, refresh_token: str) -> KeycloakTokenBundle:
    payload = await _post_form(
        {
            "grant_type": "refresh_token",
            "client_id": settings.keycloak_client_id,
            "refresh_token": refresh_token,
        }
    )
    return KeycloakTokenBundle(
        access_token=str(payload.get("access_token") or ""),
        refresh_token=str(payload.get("refresh_token") or refresh_token),
        expires_in=int(payload.get("expires_in") or 0),
        refresh_expires_in=int(payload.get("refresh_expires_in") or 0),
        id_token=str(payload.get("id_token") or "") or None,
    )


async def logout_refresh_token(*, refresh_token: str) -> None:
    async with httpx.AsyncClient(timeout=settings.keycloak_http_timeout_seconds) as client:
        response = await client.post(
            settings.keycloak_logout_endpoint,
            data={
                "client_id": settings.keycloak_client_id,
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.status_code >= 500:
        raise Forbidden("Keycloak logout failed")


async def _get_jwks() -> dict[str, Any]:
    now = time.time()
    if _jwks_cache["keys"] and (now - float(_jwks_cache["fetched_at"])) < settings.keycloak_jwks_cache_ttl_seconds:
        return _jwks_cache["keys"]

    try:
        async with httpx.AsyncClient(timeout=settings.keycloak_http_timeout_seconds) as client:
            response = await client.get(settings.keycloak_jwks_uri)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise Unauthorized("Unable to validate token") from exc
    payload = response.json()
    if not isinstance(payload, dict) or "keys" not in payload:
        raise Unauthorized("Invalid Keycloak JWKS")
    _jwks_cache["keys"] = payload
    _jwks_cache["fetched_at"] = now
    return payload


def looks_like_keycloak_token(token: str) -> bool:
    if not settings.keycloak_enabled:
        return False
    try:
        claims = jwt.get_unverified_claims(token)
    except JWTError:
        return False
    issuer = str(claims.get("iss") or "").rstrip("/")
    return issuer == settings.resolved_keycloak_issuer_url.rstrip("/")


async def decode_keycloak_access_token(token: str) -> KeycloakAccessTokenClaims:
    try:
        header = jwt.get_unverified_header(token)
        unverified = jwt.get_unverified_claims(token)
    except JWTError as exc:
        raise Unauthorized("Invalid token") from exc

    issuer = str(unverified.get("iss") or "").rstrip("/")
    if issuer != settings.resolved_keycloak_issuer_url.rstrip("/"):
        raise Unauthorized("Invalid token issuer")

    kid = str(header.get("kid") or "").strip()
    if not kid:
        raise Unauthorized("Invalid token")

    jwks = await _get_jwks()
    key = next((item for item in jwks.get("keys", []) if item.get("kid") == kid), None)
    if key is None:
        _jwks_cache["keys"] = None
        jwks = await _get_jwks()
        key = next((item for item in jwks.get("keys", []) if item.get("kid") == kid), None)
    if key is None:
        raise Unauthorized("Unknown token key")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[str(header.get("alg") or "RS256")],
            issuer=settings.resolved_keycloak_issuer_url,
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise Unauthorized("Invalid token") from exc

    audience = payload.get("aud")
    authorized_party = str(payload.get("azp") or "").strip()
    audience_values = audience if isinstance(audience, list) else [audience]
    if settings.keycloak_client_id not in [str(item) for item in audience_values if item] and authorized_party != settings.keycloak_client_id:
        raise Unauthorized("Invalid token audience")

    subject = str(payload.get("sub") or "").strip()
    issued_at = payload.get("iat")
    expires_at = payload.get("exp")
    if not subject or not isinstance(issued_at, int) or not isinstance(expires_at, int):
        raise Unauthorized("Invalid token payload")

    realm_access = payload.get("realm_access") or {}
    realm_roles_raw = realm_access.get("roles") if isinstance(realm_access, dict) else []
    realm_roles = frozenset(str(item) for item in realm_roles_raw if isinstance(item, str) and item.strip())
    return KeycloakAccessTokenClaims(
        subject=subject,
        issuer=issuer,
        issued_at=issued_at,
        expires_at=expires_at,
        preferred_username=str(payload.get("preferred_username") or "").strip() or None,
        full_name=str(payload.get("name") or "").strip() or None,
        given_name=str(payload.get("given_name") or "").strip() or None,
        family_name=str(payload.get("family_name") or "").strip() or None,
        email=str(payload.get("email") or "").strip() or None,
        email_verified=bool(payload.get("email_verified")),
        realm_roles=realm_roles,
    )
