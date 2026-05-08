from __future__ import annotations

import argparse
import ast
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REQUIRED_APP_ROLES = (
    "app.superadmin",
    "app.admin",
    "app.project_manager",
    "app.lead_economist",
    "app.economist",
    "app.operator",
    "app.contractor",
)
REQUIRED_SERVICE_ROLES = ("query-users", "view-users", "manage-users")


@dataclass
class CheckLine:
    level: str
    message: str


class Report:
    def __init__(self) -> None:
        self.lines: list[CheckLine] = []

    def ok(self, message: str) -> None:
        self.lines.append(CheckLine("OK", message))

    def warn(self, message: str) -> None:
        self.lines.append(CheckLine("WARN", message))

    def fail(self, message: str) -> None:
        self.lines.append(CheckLine("FAIL", message))

    def has_failures(self) -> bool:
        return any(line.level == "FAIL" for line in self.lines)

    def print(self) -> None:
        for line in self.lines:
            print(f"[{line.level}] {line.message}")


class HttpResponseError(RuntimeError):
    def __init__(self, *, status_code: int, body: str) -> None:
        super().__init__(f"HTTP {status_code}: {body[:500]}")
        self.status_code = status_code
        self.body = body


class SimpleHttp:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        form_data: dict[str, str] | None = None,
    ) -> tuple[int, bytes]:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        data_bytes = None
        request_headers = dict(headers or {})
        if form_data is not None:
            data_bytes = urlencode(form_data).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

        request = Request(url=f"{url}{query}", data=data_bytes, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.getcode(), response.read()
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise HttpResponseError(status_code=exc.code, body=body) from exc
        except URLError as exc:
            raise RuntimeError(f"Network error: {exc}") from exc

    def get_json(self, *, url: str, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> Any:
        _, payload = self.request(method="GET", url=url, headers=headers, params=params)
        return json.loads(payload.decode("utf-8"))

    def post_form_json(self, *, url: str, form_data: dict[str, str], headers: dict[str, str] | None = None) -> Any:
        _, payload = self.request(method="POST", url=url, headers=headers, form_data=form_data)
        return json.loads(payload.decode("utf-8"))


def _load_known_permissions_from_source() -> set[str]:
    source_path = Path(__file__).resolve().parents[1] / "domain" / "permissions.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    permissions: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "PermissionCodes":
            continue
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
                continue
            target = statement.targets[0]
            if not target.id.isupper():
                continue
            value = statement.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                permissions.add(value.value)
    return permissions


def _load_env_file(path: str) -> dict[str, str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Env file not found: {path}")

    result: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'")):
                value = value[1:-1]
            result[key] = value
    return result


def _coalesce(env_map: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        value = os.getenv(key) or env_map.get(key)
        if value:
            return value.strip()
    return default


class KeycloakAdminApi:
    def __init__(
        self,
        *,
        internal_base_url: str,
        realm: str,
        admin_realm: str,
        report: Report,
        env_map: dict[str, str],
        http: SimpleHttp,
    ) -> None:
        self._internal_base_url = internal_base_url.rstrip("/")
        self._realm = realm
        self._admin_realm = admin_realm
        self._report = report
        self._env_map = env_map
        self._http = http
        self._token = ""

    @property
    def token(self) -> str:
        if not self._token:
            self._token = self._authenticate()
        return self._token

    def _authenticate(self) -> str:
        admin_user = _coalesce(self._env_map, "KC_BOOTSTRAP_ADMIN_USERNAME", "KEYCLOAK_ADMIN_USERNAME")
        admin_password = _coalesce(self._env_map, "KC_BOOTSTRAP_ADMIN_PASSWORD", "KEYCLOAK_ADMIN_PASSWORD")
        admin_client_secret = _coalesce(self._env_map, "KEYCLOAK_ADMIN_CLIENT_SECRET")
        admin_client_id = _coalesce(self._env_map, "KEYCLOAK_ADMIN_CLIENT_ID", default="acom-admin-service")

        token_endpoint = f"{self._internal_base_url}/realms/{self._admin_realm}/protocol/openid-connect/token"

        if admin_user and admin_password:
            try:
                payload = self._http.post_form_json(
                    url=token_endpoint,
                    form_data={
                        "grant_type": "password",
                        "client_id": "admin-cli",
                        "username": admin_user,
                        "password": admin_password,
                    },
                )
                token = str(payload.get("access_token") or "").strip()
                if token:
                    self._report.ok("Authenticated in Keycloak admin API via KC bootstrap admin user")
                    return token
            except Exception:  # noqa: BLE001
                pass

        if admin_client_id and admin_client_secret:
            try:
                payload = self._http.post_form_json(
                    url=token_endpoint,
                    form_data={
                        "grant_type": "client_credentials",
                        "client_id": admin_client_id,
                        "client_secret": admin_client_secret,
                    },
                )
                token = str(payload.get("access_token") or "").strip()
                if token:
                    self._report.ok("Authenticated in Keycloak admin API via client credentials")
                    return token
            except Exception:  # noqa: BLE001
                pass

        raise RuntimeError("Unable to authenticate in Keycloak admin API")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        url = f"{self._internal_base_url}{path}"
        return self._http.get_json(url=url, headers=self._headers(), params=params)

    def get_client(self, client_id: str) -> dict[str, Any] | None:
        payload = self.get(f"/admin/realms/{self._realm}/clients", params={"clientId": client_id})
        if not isinstance(payload, list):
            return None
        for item in payload:
            if not isinstance(item, dict):
                continue
            if str(item.get("clientId") or "") == client_id:
                return item
        return None

    def get_client_roles(self, client_uuid: str) -> list[dict[str, Any]]:
        payload = self.get(f"/admin/realms/{self._realm}/clients/{client_uuid}/roles", params={"max": 2000})
        return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []

    def get_client_role(self, client_uuid: str, role_name: str) -> dict[str, Any] | None:
        try:
            payload = self.get(f"/admin/realms/{self._realm}/clients/{client_uuid}/roles/{role_name}")
        except HttpResponseError as exc:
            if exc.status_code == 404:
                return None
            raise
        return payload if isinstance(payload, dict) else None

    def get_role_composites(self, client_uuid: str, role_name: str) -> list[dict[str, Any]]:
        payload = self.get(f"/admin/realms/{self._realm}/clients/{client_uuid}/roles/{role_name}/composites")
        return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def _check_realm_and_oidc(
    report: Report,
    *,
    internal_base: str,
    public_issuer: str,
    realm: str,
    admin_api: KeycloakAdminApi,
    http: SimpleHttp,
) -> None:
    try:
        realm_payload = admin_api.get(f"/admin/realms/{realm}")
    except Exception as exc:  # noqa: BLE001
        report.fail(f"Realm '{realm}' check failed: {exc}")
        return

    if not isinstance(realm_payload, dict):
        report.fail(f"Realm '{realm}' response is invalid")
        return

    if realm_payload.get("enabled"):
        report.ok(f"Realm '{realm}' exists and enabled")
    else:
        report.fail(f"Realm '{realm}' is disabled")

    well_known = f"{public_issuer.rstrip('/')}/.well-known/openid-configuration"
    try:
        oidc = http.get_json(url=well_known)
    except Exception as exc:  # noqa: BLE001
        report.fail(f"OIDC discovery unavailable: {exc}")
        return

    issuer = str((oidc or {}).get("issuer") or "").rstrip("/")
    if issuer == public_issuer.rstrip("/"):
        report.ok(f"Issuer matches expected '{public_issuer}'")
    else:
        report.fail(f"Issuer mismatch: expected '{public_issuer}', got '{issuer}'")

    jwks_uri = str((oidc or {}).get("jwks_uri") or "").strip()
    if not jwks_uri:
        report.fail("JWKS URI is missing in OIDC discovery")
        return

    try:
        _ = http.get_json(url=jwks_uri)
        report.ok("JWKS endpoint is accessible")
    except Exception as exc:  # noqa: BLE001
        report.fail(f"JWKS endpoint check failed: {exc}")

    report.ok(f"Keycloak internal base URL reachable via admin API '{internal_base}'")


def _check_web_client(report: Report, admin_api: KeycloakAdminApi, client_id: str, backend_base_url: str, web_base_url: str) -> None:
    client = admin_api.get_client(client_id)
    if client is None:
        report.fail(f"Client '{client_id}' is missing")
        return

    report.ok(f"Client '{client_id}' exists")

    expected_redirect = f"{backend_base_url.rstrip('/')}/api/v1/auth/callback"
    redirect_uris = set(client.get("redirectUris") or [])
    web_origins = set(client.get("webOrigins") or [])

    checks = (
        (bool(client.get("publicClient")), "public client"),
        (bool(client.get("standardFlowEnabled")), "standard flow enabled"),
        (not bool(client.get("implicitFlowEnabled")), "implicit flow disabled"),
        (not bool(client.get("directAccessGrantsEnabled")), "direct access grants disabled"),
        (not bool(client.get("serviceAccountsEnabled")), "service accounts disabled"),
        (expected_redirect in redirect_uris, f"redirect URI contains '{expected_redirect}'"),
        (web_base_url.rstrip("/") in web_origins, f"web origins contains '{web_base_url}'"),
    )

    for passed, label in checks:
        if passed:
            report.ok(f"{client_id}: {label}")
        else:
            report.fail(f"{client_id}: {label}")


def _check_api_client_roles(report: Report, admin_api: KeycloakAdminApi, api_client_id: str, strict_unknown_atomic: bool) -> str | None:
    client = admin_api.get_client(api_client_id)
    if client is None:
        report.fail(f"Client '{api_client_id}' is missing")
        return None

    report.ok(f"Client '{api_client_id}' exists")
    client_uuid = str(client.get("id") or "").strip()
    if not client_uuid:
        report.fail(f"Client '{api_client_id}' uuid is empty")
        return None

    roles = admin_api.get_client_roles(client_uuid)
    role_names = {str(role.get("name") or "").strip() for role in roles if role.get("name")}
    known_permissions = _load_known_permissions_from_source()

    missing_permissions = sorted(permission for permission in known_permissions if permission not in role_names)
    if missing_permissions:
        report.fail(f"Missing PermissionCodes in Keycloak '{api_client_id}': {', '.join(missing_permissions)}")
    else:
        report.ok(f"All PermissionCodes are present in '{api_client_id}'")

    unknown_roles = sorted(
        role_name
        for role_name in role_names
        if role_name not in known_permissions and not role_name.startswith("app.") and not role_name.startswith("delegation.")
    )
    if unknown_roles:
        message = f"Unknown non-app/delegation roles in '{api_client_id}': {', '.join(unknown_roles)}"
        if strict_unknown_atomic:
            report.fail(message)
        else:
            report.warn(message)

    for app_role in REQUIRED_APP_ROLES:
        role_payload = admin_api.get_client_role(client_uuid, app_role)
        if role_payload is None:
            report.fail(f"Missing required role '{app_role}'")
            continue
        if bool(role_payload.get("composite")):
            report.ok(f"Role '{app_role}' exists and composite")
        else:
            report.fail(f"Role '{app_role}' exists but is not composite")

    superadmin_composites = admin_api.get_role_composites(client_uuid, "app.superadmin")
    superadmin_names = {
        str(item.get("name") or "").strip()
        for item in superadmin_composites
        if isinstance(item, dict) and item.get("name")
    }
    missing_from_superadmin = sorted(permission for permission in known_permissions if permission not in superadmin_names)
    if missing_from_superadmin:
        report.fail("app.superadmin does not include all PermissionCodes")
    else:
        report.ok("app.superadmin includes all PermissionCodes")

    delegation_roles = sorted(role for role in role_names if role.startswith("delegation."))
    if not delegation_roles:
        report.ok("no delegation roles found")
    else:
        report.ok(f"delegation roles found: {', '.join(delegation_roles)}")
        for delegation_role in delegation_roles:
            role_payload = admin_api.get_client_role(client_uuid, delegation_role)
            if role_payload is None:
                report.warn(f"delegation role '{delegation_role}' lookup failed")
                continue
            if bool(role_payload.get("composite")):
                composites = admin_api.get_role_composites(client_uuid, delegation_role)
                report.ok(f"{delegation_role}: composite, nested roles={len(composites)}")
            else:
                report.warn(f"{delegation_role}: non-composite delegation role")

    return client_uuid


def _check_admin_service_client(
    report: Report,
    admin_api: KeycloakAdminApi,
    client_id: str,
    realm: str,
    env_map: dict[str, str],
    http: SimpleHttp,
) -> None:
    client = admin_api.get_client(client_id)
    if client is None:
        report.fail(f"Client '{client_id}' is missing")
        return

    report.ok(f"Client '{client_id}' exists")

    if not bool(client.get("publicClient")):
        report.ok(f"{client_id}: confidential client")
    else:
        report.fail(f"{client_id}: expected confidential client")

    if bool(client.get("serviceAccountsEnabled")):
        report.ok(f"{client_id}: service account enabled")
    else:
        report.fail(f"{client_id}: service account disabled")

    client_secret = _coalesce(env_map, "KEYCLOAK_ADMIN_CLIENT_SECRET")
    if not client_secret:
        report.warn("KEYCLOAK_ADMIN_CLIENT_SECRET is not set, cannot verify service-account token directly")
    else:
        token_endpoint = (
            f"{_coalesce(env_map, 'KEYCLOAK_INTERNAL_BASE_URL', default='http://keycloak:8080/iam').rstrip('/')}/"
            f"realms/{realm}/protocol/openid-connect/token"
        )
        try:
            payload = http.post_form_json(
                url=token_endpoint,
                form_data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
            token = str(payload.get("access_token") or "").strip()
            if token:
                report.ok(f"{client_id}: service account token request succeeded")
            else:
                report.fail(f"{client_id}: service account token request returned empty token")
        except Exception as exc:  # noqa: BLE001
            report.fail(f"{client_id}: service account token request failed: {exc}")

    service_account_user_id = str(client.get("serviceAccountUserId") or "").strip()
    if not service_account_user_id:
        client_uuid = str(client.get("id") or "").strip()
        if client_uuid:
            try:
                service_account_user = admin_api.get(
                    f"/admin/realms/{realm}/clients/{client_uuid}/service-account-user"
                )
                if isinstance(service_account_user, dict):
                    service_account_user_id = str(service_account_user.get("id") or "").strip()
            except Exception:  # noqa: BLE001
                service_account_user_id = ""

    if not service_account_user_id:
        report.fail(f"{client_id}: missing serviceAccountUserId")
        return

    realm_management = admin_api.get_client("realm-management")
    if realm_management is None:
        report.fail("Client 'realm-management' is missing")
        return

    realm_management_uuid = str(realm_management.get("id") or "").strip()
    if not realm_management_uuid:
        report.fail("Client 'realm-management' uuid is empty")
        return

    mappings = admin_api.get(
        f"/admin/realms/{realm}/users/{service_account_user_id}/role-mappings/clients/{realm_management_uuid}"
    )
    mapping_names = {
        str(item.get("name") or "").strip()
        for item in mappings
        if isinstance(item, dict) and item.get("name")
    }

    for required_role in REQUIRED_SERVICE_ROLES:
        if required_role in mapping_names:
            report.ok(f"{client_id}: has realm-management role '{required_role}'")
        else:
            report.fail(f"{client_id}: missing realm-management role '{required_role}'")


def _check_bootstrap_superadmin(report: Report, admin_api: KeycloakAdminApi, realm: str, api_client_uuid: str | None, api_client_id: str, env_map: dict[str, str]) -> None:
    bootstrap_username = _coalesce(env_map, "KEYCLOAK_BOOTSTRAP_APP_USERNAME", default="superadmin")
    users_payload = admin_api.get(
        f"/admin/realms/{realm}/users",
        params={"username": bootstrap_username, "exact": "true"},
    )
    users = [item for item in users_payload if isinstance(item, dict)] if isinstance(users_payload, list) else []
    if not users:
        report.fail(f"Bootstrap user '{bootstrap_username}' not found")
        return

    user = users[0]
    user_id = str(user.get("id") or "").strip()
    if bool(user.get("enabled")):
        report.ok(f"Bootstrap user '{bootstrap_username}' is enabled")
    else:
        report.fail(f"Bootstrap user '{bootstrap_username}' is disabled")

    if not api_client_uuid:
        report.fail(f"Cannot verify bootstrap role mapping: client '{api_client_id}' uuid is missing")
        return

    mappings_payload = admin_api.get(
        f"/admin/realms/{realm}/users/{user_id}/role-mappings/clients/{api_client_uuid}"
    )
    role_names = {
        str(item.get("name") or "").strip()
        for item in mappings_payload
        if isinstance(item, dict) and item.get("name")
    }
    if "app.superadmin" in role_names:
        report.ok(f"Bootstrap user '{bootstrap_username}' has app.superadmin")
    else:
        report.fail(f"Bootstrap user '{bootstrap_username}' is missing app.superadmin")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Keycloak permission model checks")
    parser.add_argument("--env-file", required=True, help="Path to env file")
    parser.add_argument("--strict-unknown-atomic", action="store_true", help="Fail on unknown non-app/delegation roles")
    args = parser.parse_args()

    env_map = _load_env_file(args.env_file)
    report = Report()

    timeout = float(_coalesce(env_map, "KEYCLOAK_HTTP_TIMEOUT_SECONDS", default="10") or "10")
    http = SimpleHttp(timeout=timeout)

    internal_base = _coalesce(env_map, "KEYCLOAK_INTERNAL_BASE_URL", default="http://keycloak:8080/iam")
    realm = _coalesce(env_map, "KEYCLOAK_REALM", default="acom-offerdesk")
    admin_realm = _coalesce(env_map, "KEYCLOAK_ADMIN_REALM", default="master")
    web_base_url = _coalesce(env_map, "WEB_BASE_URL", default="http://localhost:8080")
    backend_base_url = _coalesce(env_map, "PUBLIC_BACKEND_BASE_URL", "WEB_BASE_URL", default="http://localhost:8080")
    issuer = _coalesce(env_map, "KEYCLOAK_ISSUER_URL")
    if not issuer:
        public_base = _coalesce(env_map, "KEYCLOAK_PUBLIC_BASE_URL", default=f"{web_base_url.rstrip('/')}/iam")
        issuer = f"{public_base.rstrip('/')}/realms/{realm}"

    web_client_id = _coalesce(env_map, "KEYCLOAK_WEB_CLIENT_ID", "KEYCLOAK_CLIENT_ID", default="acom-web")
    api_client_id = _coalesce(env_map, "KEYCLOAK_API_CLIENT_ID", default="acom-api")
    admin_service_client_id = _coalesce(env_map, "KEYCLOAK_ADMIN_CLIENT_ID", default="acom-admin-service")

    try:
        admin_api = KeycloakAdminApi(
            internal_base_url=internal_base,
            realm=realm,
            admin_realm=admin_realm,
            report=report,
            env_map=env_map,
            http=http,
        )
        _ = admin_api.token
    except Exception as exc:  # noqa: BLE001
        report.fail(f"Admin API authentication failed: {exc}")
        report.print()
        return 1

    _check_realm_and_oidc(
        report,
        internal_base=internal_base,
        public_issuer=issuer,
        realm=realm,
        admin_api=admin_api,
        http=http,
    )
    _check_web_client(
        report,
        admin_api,
        web_client_id,
        backend_base_url,
        web_base_url,
    )
    api_client_uuid = _check_api_client_roles(
        report,
        admin_api,
        api_client_id,
        strict_unknown_atomic=args.strict_unknown_atomic,
    )
    _check_admin_service_client(
        report,
        admin_api,
        admin_service_client_id,
        realm,
        env_map,
        http,
    )
    _check_bootstrap_superadmin(
        report,
        admin_api,
        realm,
        api_client_uuid,
        api_client_id,
        env_map,
    )

    report.print()
    return 1 if report.has_failures() else 0


if __name__ == "__main__":
    raise SystemExit(main())
