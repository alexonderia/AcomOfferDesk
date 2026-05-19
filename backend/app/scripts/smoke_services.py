from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlsplit
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from urllib.error import HTTPError, URLError


CRITICAL_TABLES = (
    "users",
    "roles",
    "profiles",
    "user_auth_accounts",
    "requests",
    "offers",
)


@dataclass
class CheckResult:
    level: str
    name: str
    message: str


class Reporter:
    def __init__(self) -> None:
        self.results: list[CheckResult] = []

    def ok(self, name: str, message: str) -> None:
        self.results.append(CheckResult("OK", name, message))

    def warn(self, name: str, message: str) -> None:
        self.results.append(CheckResult("WARN", name, message))

    def fail(self, name: str, message: str) -> None:
        self.results.append(CheckResult("FAIL", name, message))

    def has_failures(self) -> bool:
        return any(item.level == "FAIL" for item in self.results)

    def print(self) -> None:
        for item in self.results:
            print(f"[{item.level}] {item.name}: {item.message}")


def _load_env_file(path: str) -> dict[str, str]:
    env_map: dict[str, str] = {}
    if not os.path.exists(path):
        raise FileNotFoundError(f"Env file not found: {path}")

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
            env_map[key] = value
    return env_map


def _coalesce(env_map: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        value = os.getenv(key) or env_map.get(key)
        if value:
            return value.strip()
    return default


def _to_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on"}


def _normalize_postgres_dsn_for_asyncpg(dsn: str) -> str:
    normalized = dsn.strip()
    if "://" not in normalized:
        return normalized
    scheme, rest = normalized.split("://", 1)
    if "+" in scheme:
        base_scheme = scheme.split("+", 1)[0]
        if base_scheme in {"postgresql", "postgres"}:
            return f"{base_scheme}://{rest}"
    return normalized


def _is_internal_hostname(host: str) -> bool:
    candidate = (host or "").strip().strip("[]")
    if not candidate:
        return False
    if ":" in candidate and candidate.count(":") == 1 and "." not in candidate:
        candidate = candidate.split(":", 1)[0]
    if candidate in {"localhost", "127.0.0.1", "::1"}:
        return False
    try:
        ip_address(candidate)
        return False
    except ValueError:
        pass
    return "." not in candidate


def _host_hint(host: str, *, env_name: str) -> str:
    if _is_internal_hostname(host):
        return f" Host '{host}' looks like an internal Docker DNS name. Override via {env_name}."
    return ""


def _parse_endpoint_host_port(endpoint: str, *, default_secure: bool) -> tuple[str, bool]:
    value = endpoint.strip()
    if "://" not in value:
        return value, default_secure

    parsed = urlsplit(value)
    if parsed.path not in {"", "/"}:
        raise ValueError("S3 endpoint must not include path")
    if not parsed.netloc:
        raise ValueError("S3 endpoint URL must include host")
    secure = parsed.scheme.lower() == "https"
    return parsed.netloc, secure


async def _check_http(
    reporter: Reporter,
    *,
    name: str,
    url: str,
    accepted_codes: set[int],
    timeout: float,
    critical: bool,
    retries: int,
) -> None:
    message = ""
    for attempt in range(max(0, retries) + 1):
        try:
            request = Request(url=url, method="GET")
            with urlopen(request, timeout=timeout) as response:
                status_code = response.getcode()
            if status_code in accepted_codes:
                reporter.ok(name, f"{url} ({status_code})")
                return
            message = f"{url} returned status {status_code}"
        except HTTPError as exc:
            if exc.code in accepted_codes:
                reporter.ok(name, f"{url} ({exc.code})")
                return
            message = f"{url} returned status {exc.code}"
        except URLError as exc:
            message = f"{url} error: {exc}"
        except Exception as exc:  # noqa: BLE001
            message = f"{url} error: {exc}"

        if attempt < retries:
            await asyncio.sleep(0.6 * (attempt + 1))

    if critical:
        reporter.fail(name, message)
    else:
        reporter.warn(name, message)


async def _check_postgres(reporter: Reporter, env_map: dict[str, str]) -> None:
    raw_database_url = _coalesce(env_map, "SMOKE_DATABASE_URL", "DATABASE_URL")
    database_url = _normalize_postgres_dsn_for_asyncpg(raw_database_url)
    if not database_url:
        reporter.fail("PostgreSQL", "DATABASE_URL is missing")
        return

    try:
        import asyncpg  # type: ignore
    except ImportError:
        reporter.warn("PostgreSQL", "asyncpg is not installed, DB checks skipped")
        return

    try:
        conn = await asyncpg.connect(database_url, timeout=7)
    except Exception as exc:  # noqa: BLE001
        host = ""
        try:
            host = urlsplit(database_url).hostname or ""
        except Exception:  # noqa: BLE001
            host = ""
        hint = _host_hint(host, env_name="SMOKE_DATABASE_URL")
        message = f"Unable to connect: {exc}"
        if hint:
            message += hint
        reporter.fail("PostgreSQL", message)
        return

    try:
        value = await conn.fetchval("SELECT 1")
        if value == 1:
            reporter.ok("PostgreSQL", "SELECT 1 succeeded")
        else:
            reporter.fail("PostgreSQL", f"Unexpected SELECT 1 result: {value}")

        existing_tables = {
            row["table_name"]
            for row in await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        }
        missing = [table for table in CRITICAL_TABLES if table not in existing_tables]
        if missing:
            reporter.warn("PostgreSQL", f"Missing expected tables: {', '.join(missing)}")
        else:
            reporter.ok("PostgreSQL", "Critical tables exist")
    except Exception as exc:  # noqa: BLE001
        reporter.fail("PostgreSQL", f"Query failed: {exc}")
    finally:
        await conn.close()


async def _check_keycloak(reporter: Reporter, env_map: dict[str, str], timeout: float, base_url: str) -> None:
    keycloak_enabled = _to_bool(_coalesce(env_map, "KEYCLOAK_ENABLED", default="false"))
    if not keycloak_enabled:
        reporter.warn("Keycloak", "KEYCLOAK_ENABLED=false, checks skipped")
        return

    realm = _coalesce(env_map, "KEYCLOAK_REALM", default="acom-offerdesk")
    issuer_expected = _coalesce(env_map, "KEYCLOAK_ISSUER_URL")
    if not issuer_expected:
        public_base = _coalesce(env_map, "KEYCLOAK_PUBLIC_BASE_URL") or urljoin(base_url.rstrip("/") + "/", "iam")
        issuer_expected = f"{public_base.rstrip('/')}/realms/{realm}"

    well_known = f"{issuer_expected.rstrip('/')}/.well-known/openid-configuration"
    try:
        request = Request(url=well_known, method="GET")
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        reporter.fail("Keycloak issuer", f"{well_known} unavailable: {exc}")
        return

    resolved_issuer = str(payload.get("issuer") or "").rstrip("/")
    if resolved_issuer != issuer_expected.rstrip("/"):
        reporter.fail("Keycloak issuer", f"issuer mismatch: expected {issuer_expected}, got {resolved_issuer}")
    else:
        reporter.ok("Keycloak issuer", resolved_issuer)

    jwks_uri = str(payload.get("jwks_uri") or "").strip()
    if not jwks_uri:
        reporter.fail("Keycloak JWKS", "jwks_uri is missing in openid configuration")
        return

    await _check_http(
        reporter,
        name="Keycloak JWKS",
        url=jwks_uri,
        accepted_codes={200},
        timeout=timeout,
        critical=True,
        retries=int(_coalesce(env_map, "SMOKE_HTTP_RETRIES", default="2") or "2"),
    )


def _minio_smoke_probe(
    endpoint: str,
    *,
    access_key: str,
    secret_key: str,
    secure: bool,
    bucket: str,
) -> tuple[bool, str | None]:
    """Sync MinIO probe: (bucket_exists, list_error_message or None if list OK)."""
    from minio import Minio  # type: ignore

    client = Minio(
        endpoint,
        access_key=access_key or None,
        secret_key=secret_key or None,
        secure=secure,
    )
    if not client.bucket_exists(bucket):
        return False, None
    try:
        _ = next(client.list_objects(bucket, recursive=False), None)
    except Exception as exc:  # noqa: BLE001
        return True, str(exc)
    return True, None


async def _check_s3_minio(reporter: Reporter, env_map: dict[str, str]) -> None:
    if _to_bool(_coalesce(env_map, "SMOKE_SKIP_MINIO", default="false")):
        reporter.warn("S3/MinIO", "SMOKE_SKIP_MINIO=true, check skipped")
        return

    endpoint_raw = _coalesce(env_map, "SMOKE_S3_ENDPOINT", "S3_PUBLIC_ENDPOINT", "S3_ENDPOINT")
    bucket = _coalesce(env_map, "S3_BUCKET")
    access_key = _coalesce(env_map, "SMOKE_S3_ACCESS_KEY", "S3_ACCESS_KEY")
    secret_key = _coalesce(env_map, "SMOKE_S3_SECRET_KEY", "S3_SECRET_KEY")
    secure = _to_bool(_coalesce(env_map, "SMOKE_S3_SECURE", "S3_SECURE", default="false"))
    timeout = float(_coalesce(env_map, "SMOKE_MINIO_TIMEOUT_SECONDS", default="10") or "10")

    if not endpoint_raw or not bucket:
        reporter.warn("S3/MinIO", "S3_ENDPOINT or S3_BUCKET is missing, check skipped")
        return

    try:
        endpoint, secure = _parse_endpoint_host_port(endpoint_raw, default_secure=secure)
    except ValueError as exc:
        reporter.fail("S3/MinIO", f"Invalid endpoint '{endpoint_raw}': {exc}")
        return

    try:
        from minio import Minio  # type: ignore  # noqa: F401
    except ImportError:
        reporter.warn("S3/MinIO", "minio package is not installed, check skipped")
        return

    try:
        exists, list_error = await asyncio.wait_for(
            asyncio.to_thread(
                _minio_smoke_probe,
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
                bucket=bucket,
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        host_hint = _host_hint(endpoint, env_name="SMOKE_S3_ENDPOINT")
        message = f"MinIO check timed out after {timeout:.0f}s (endpoint={endpoint})"
        if host_hint:
            message += host_hint
        reporter.fail("S3/MinIO", message)
        return
    except Exception as exc:  # noqa: BLE001
        host_hint = _host_hint(endpoint, env_name="SMOKE_S3_ENDPOINT")
        message = f"Bucket check failed: {exc}"
        if host_hint:
            message += host_hint
        reporter.fail("S3/MinIO", message)
        return

    if not exists:
        reporter.fail("S3/MinIO", f"Bucket '{bucket}' does not exist")
        return

    reporter.ok("S3/MinIO", f"Bucket '{bucket}' exists")
    if list_error:
        reporter.warn("S3/MinIO", f"List objects failed: {list_error}")
    else:
        reporter.ok("S3/MinIO", "List objects succeeded (non-destructive)")


async def _check_rabbitmq(reporter: Reporter, env_map: dict[str, str]) -> None:
    rabbitmq_url = _coalesce(env_map, "SMOKE_RABBITMQ_URL", "RABBITMQ_URL")
    if not rabbitmq_url:
        reporter.warn("RabbitMQ", "RABBITMQ_URL is missing, check skipped")
        return

    try:
        import aio_pika  # type: ignore
    except ImportError:
        reporter.warn("RabbitMQ", "aio-pika is not installed, check skipped")
        return

    try:

        async def _connect_and_close() -> None:
            connection = await aio_pika.connect_robust(rabbitmq_url, timeout=7)
            await connection.close()

        await asyncio.wait_for(_connect_and_close(), timeout=15.0)
        reporter.ok("RabbitMQ", "AMQP connection succeeded")
    except TimeoutError:
        reporter.fail("RabbitMQ", "AMQP connection timed out after 15s")
    except Exception as exc:  # noqa: BLE001
        host = ""
        try:
            host = urlsplit(rabbitmq_url).hostname or ""
        except Exception:  # noqa: BLE001
            host = ""
        hint = _host_hint(host, env_name="SMOKE_RABBITMQ_URL")
        message = f"AMQP connection failed: {exc}"
        if hint:
            message += hint
        reporter.fail("RabbitMQ", message)


async def run_checks(
    env_file: str,
    base_url: str | None,
    database_url: str | None,
    s3_endpoint: str | None,
    rabbitmq_url: str | None,
) -> int:
    env_map = _load_env_file(env_file)
    if database_url:
        env_map["SMOKE_DATABASE_URL"] = database_url
    if s3_endpoint:
        env_map["SMOKE_S3_ENDPOINT"] = s3_endpoint
    if rabbitmq_url:
        env_map["SMOKE_RABBITMQ_URL"] = rabbitmq_url
    reporter = Reporter()

    resolved_base_url = (base_url or _coalesce(env_map, "WEB_BASE_URL", "PUBLIC_BACKEND_BASE_URL", default="http://localhost:8080")).rstrip("/")
    timeout = float(_coalesce(env_map, "SMOKE_HTTP_TIMEOUT_SECONDS", default="10") or "10")
    retries = int(_coalesce(env_map, "SMOKE_HTTP_RETRIES", default="2") or "2")

    await _check_http(
        reporter,
        name="Gateway/Web root",
        url=f"{resolved_base_url}/",
        accepted_codes={200, 301, 302, 307, 308},
        timeout=timeout,
        critical=True,
        retries=retries,
    )

    await _check_http(
        reporter,
        name="Backend health",
        url=f"{resolved_base_url}/health",
        accepted_codes={200},
        timeout=timeout,
        critical=True,
        retries=retries,
    )

    await _check_http(
        reporter,
        name="API proxy",
        url=f"{resolved_base_url}/api/v1/auth/oidc/login?next_path=%2F",
        accepted_codes={200, 302, 303, 307, 308, 401, 403},
        timeout=timeout,
        critical=True,
        retries=retries,
    )

    realm = _coalesce(env_map, "KEYCLOAK_REALM", default="acom-offerdesk")
    await _check_http(
        reporter,
        name="Gateway /iam",
        url=f"{resolved_base_url}/iam/realms/{realm}",
        accepted_codes={200, 301, 302, 307, 308},
        timeout=timeout,
        critical=False,
        retries=retries,
    )

    await _check_postgres(reporter, env_map)
    await _check_keycloak(reporter, env_map, timeout, resolved_base_url)
    await _check_s3_minio(reporter, env_map)
    if _to_bool(_coalesce(env_map, "SMOKE_SKIP_RABBITMQ", default="false")):
        reporter.warn("RabbitMQ", "SMOKE_SKIP_RABBITMQ=true, check skipped")
    else:
        await _check_rabbitmq(reporter, env_map)

    reporter.print()
    return 1 if reporter.has_failures() else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Non-destructive infrastructure smoke checks")
    parser.add_argument("--env-file", required=True, help="Path to env file")
    parser.add_argument("--base-url", default=None, help="Gateway/Web base URL (e.g. http://localhost:8080)")
    parser.add_argument("--database-url", default=None, help="Override DB URL for smoke checks")
    parser.add_argument("--s3-endpoint", default=None, help="Override S3 endpoint (host:port or http(s)://host:port)")
    parser.add_argument("--rabbitmq-url", default=None, help="Override RabbitMQ URL for smoke checks")
    args = parser.parse_args()

    return asyncio.run(
        run_checks(
            env_file=args.env_file,
            base_url=args.base_url,
            database_url=args.database_url,
            s3_endpoint=args.s3_endpoint,
            rabbitmq_url=args.rabbitmq_url,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
