from __future__ import annotations

from app.core.config import settings
from app.domain.exceptions import ServiceUnavailable, UploadRejected
from app.domain.permissions import PermissionCodes
from app.services import file_upload_guard as file_upload_guard_module


def test_request_upload_returns_reason_code_when_guard_blocks(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
) -> None:
    async def _blocked(self, *, original_name: str, content_bytes: bytes, content_type: str | None):
        _ = (self, original_name, content_bytes, content_type)
        raise UploadRejected(
            reason_code="mime_mismatch",
            detail="Содержимое файла не соответствует расширению файла.",
        )

    monkeypatch.setattr(file_upload_guard_module.FileUploadGuardService, "scan_bytes", _blocked)
    set_uow(object())
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.REQUESTS_FILES_UPLOAD, PermissionCodes.REQUESTS_UPDATE},
        )
    )

    response = test_client.post(
        "/api/v1/requests/10/files",
        files={"file": ("wrong.pdf", b"not-a-pdf", "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Содержимое файла не соответствует расширению файла.",
        "reason_code": "mime_mismatch",
    }


def test_request_upload_returns_safe_message_when_guard_is_unavailable(
    test_client,
    monkeypatch,
    set_current_user,
    set_uow,
    make_current_user,
) -> None:
    async def _unavailable(self, *, original_name: str, content_bytes: bytes, content_type: str | None):
        _ = (self, original_name, content_bytes, content_type)
        raise ServiceUnavailable(
            reason_code="file_scan_unavailable",
            detail="Файл не удалось проверить. Попробуйте загрузить его позже.",
        )

    monkeypatch.setattr(file_upload_guard_module.FileUploadGuardService, "scan_bytes", _unavailable)
    set_uow(object())
    set_current_user(
        make_current_user(
            user_id="owner-1",
            role_id=settings.economist_role_id,
            permissions={PermissionCodes.REQUESTS_FILES_UPLOAD, PermissionCodes.REQUESTS_UPDATE},
        )
    )

    response = test_client.post(
        "/api/v1/requests/10/files",
        files={"file": ("wrong.pdf", b"not-a-pdf", "application/pdf")},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Файл не удалось проверить. Попробуйте загрузить его позже.",
        "reason_code": "file_scan_unavailable",
    }
