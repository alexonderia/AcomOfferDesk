from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from docx import Document
import pytest

from app.api.v1 import requests as requests_api
from app.domain.permissions import PermissionCodes
from app.services.files import FileService
from app.services.requests import RequestService


class SourceUow:
    def __init__(self):
        self.requests = SimpleNamespace(
            get_by_id=AsyncMock(return_value=SimpleNamespace(id="REQ-1", id_user="owner")),
            list_hidden_files=AsyncMock(return_value=[(SimpleNamespace(id=9, path="private", name="Договор.docx"), None)]),
        )
        self.files = SimpleNamespace(
            get_hidden_request_id=AsyncMock(return_value="REQ-1"),
            is_normative_file=AsyncMock(return_value=True),  # Another link must not bypass source policy.
            get_by_id=AsyncMock(return_value=SimpleNamespace(original_name="Договор.docx", mime_type="application/octet-stream")),
        )
        self.users = SimpleNamespace(get_by_id=AsyncMock(return_value=SimpleNamespace(id_role=7)))
        self.offers = self.user_status_periods = self.economy_plans = self.notifications = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


@pytest.mark.parametrize("is_source", [True, False, None])
@pytest.mark.parametrize("role", [1, 2, 4, 5, 6, 7, 8])
def test_all_internal_roles_can_read_original_when_request_is_visible(
    test_client, set_uow, set_current_user, make_current_user, monkeypatch, role, is_source,
):
    uow = SourceUow()
    uow.requests.list_hidden_files.return_value = [(SimpleNamespace(id=9, path="private", name="Договор.docx"), is_source)]
    set_uow(uow)
    set_current_user(make_current_user(role_id=role, permissions={PermissionCodes.REQUESTS_READ}))
    scope = AsyncMock(return_value=["owner"])
    monkeypatch.setattr(RequestService, "_resolve_visible_owner_ids_for_staff_scope", scope)
    read = AsyncMock(return_value=b"original-contract")
    monkeypatch.setattr(FileService, "read_bytes", read)
    response = test_client.get("/api/v1/requests/REQ-1/source-files")
    assert response.status_code == 200
    assert response.json()["files"][0]["id"] == 9
    assert response.json()["files"][0]["is_specification_source"] is is_source
    assert response.json()["files"][0]["can_delete"] is False
    response = test_client.get("/api/v1/files/9/download")
    assert response.status_code == 200
    assert response.content == b"original-contract"
    assert response.headers["cache-control"] == "private, no-store"
    assert scope.await_count == 2


@pytest.mark.parametrize("contractor", [True, False])
@pytest.mark.parametrize("is_source", [True, False, None])
def test_originals_are_forbidden_for_contractor_or_outside_request_scope(
    test_client, set_uow, set_current_user, make_current_user, monkeypatch, contractor, is_source,
):
    uow = SourceUow()
    uow.requests.list_hidden_files.return_value = [(SimpleNamespace(id=9, path="private", name="Договор.docx"), is_source)]
    set_uow(uow)
    set_current_user(make_current_user(role_id=3 if contractor else 6,
        permissions={PermissionCodes.REQUESTS_READ, PermissionCodes.FILES_DOWNLOAD, PermissionCodes.NORMATIVE_FILES_READ}))
    monkeypatch.setattr(RequestService, "_resolve_visible_owner_ids_for_staff_scope", AsyncMock(return_value=[]))
    read = AsyncMock()
    monkeypatch.setattr(FileService, "read_bytes", read)
    assert test_client.get("/api/v1/requests/REQ-1/source-files").status_code == 403
    assert test_client.get("/api/v1/files/9/download").status_code == 403
    uow.requests.list_hidden_files.assert_not_awaited()
    read.assert_not_awaited()


@pytest.mark.parametrize("public_indices", [[], [1], [0], [0, 1]])
def test_preview_and_creation_preserve_source_separately_and_reject_tampering(
    test_client, set_current_user, set_uow, make_current_user, monkeypatch, public_indices,
):
    import base64

    document = Document()
    table = document.add_table(rows=2, cols=4)
    for row, values in zip(table.rows, (("Наименование", "Количество", "Ед. изм.", "Цена"), ("Насос", "2", "шт.", "15000"))):
        for cell, text in zip(row.cells, values):
            cell.text = text
    stream = io.BytesIO()
    document.save(stream)
    original = stream.getvalue()
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    appendix_document = Document()
    appendix_document.add_paragraph("Приложение без таблицы товаров. Сведения для сотрудников.")
    appendix_stream = io.BytesIO()
    appendix_document.save(appendix_stream)
    appendix = appendix_stream.getvalue()
    set_current_user(make_current_user(permissions={PermissionCodes.REQUESTS_CREATE, PermissionCodes.NORMATIVE_FILES_READ}))
    monkeypatch.setattr(requests_api.settings, "email_enabled", False)
    response = test_client.post("/api/v1/requests/specification-preview",
        data={"request_id": "REQ-1", "extraction_indices": "0", "public_source_indices": [str(index) for index in public_indices]},
        files=[("files", ("Договор.docx", original, mime)), ("files", ("Приложение.docx", appendix, mime))])
    assert response.status_code == 200
    preview = response.json()
    assert preview["name"] == "Заявка на закупку REQ-1.docx"
    generated = base64.b64decode(preview["content_base64"])
    assert preview["item_count"] == 1
    prepared = Document(io.BytesIO(generated))
    assert prepared.tables[0].cell(1, 0).text == "Насос"
    assert "15000" not in " ".join(cell.text for row in prepared.tables[0].rows for cell in row.cells)

    uow = SourceUow()
    uow.profiles = None
    uow.requests.create = AsyncMock(return_value=SimpleNamespace(id="REQ-1", id_user="user-1"))
    uow.requests.exists_by_id = AsyncMock(return_value=False)
    uow.requests.attach_file = AsyncMock()
    uow.requests.attach_hidden_file = AsyncMock()
    uow.requests.hide_from_contractors = AsyncMock()
    uow.files.get_normative_file_status = AsyncMock(return_value="actual")
    uow.files.get_normative_file = AsyncMock(return_value=SimpleNamespace(id_storage_object=1, original_name="Норматив.pdf"))
    uow.files.create = AsyncMock(return_value=SimpleNamespace(id=1))
    stored = []

    async def store(self, *, upload):
        stored.append(upload)
        return SimpleNamespace(id=len(stored) + 1)

    monkeypatch.setattr(FileService, "_store", store)
    monkeypatch.setattr(requests_api.EmailNotificationService, "notify_new_request", AsyncMock())
    set_uow(uow)
    data = {"id": "REQ-1", "deadline_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
            "normative_file_id": "1", "initial_amount": "100", "specification_confirmation": preview["confirmation"]}
    files = [("source_files", ("Договор.docx", original, mime)), ("source_files", ("Приложение.docx", appendix, mime)),
             ("files", (preview["name"], generated, mime))]
    tampered = test_client.post("/api/v1/requests", data={**data, "specification_confirmation": preview["confirmation"] + "bad"}, files=files)
    assert tampered.status_code == 409
    uow.requests.create.assert_not_awaited()
    changed_appendix = [files[0], ("source_files", ("Приложение.docx", original, mime)), files[2]]
    assert test_client.post("/api/v1/requests", data=data, files=changed_appendix).status_code == 409
    uow.requests.create.assert_not_awaited()
    response = test_client.post("/api/v1/requests", data=data, files=files)
    assert response.status_code == 200
    public_file_ids = [index + 2 for index in public_indices]
    assert response.json()["data"]["file_ids"] == [1, *public_file_ids, 4]
    assert [call.kwargs["file_id"] for call in uow.requests.attach_hidden_file.await_args_list] == [index + 2 for index in range(2) if index not in public_indices]
    assert [call.kwargs["is_specification_source"] for call in uow.requests.attach_hidden_file.await_args_list] == [index == 0 for index in range(2) if index not in public_indices]
    assert [call.kwargs["file_id"] for call in uow.requests.attach_file.await_args_list] == [1, *public_file_ids, 4]
    assert stored[0].content_bytes == original
    assert stored[1].content_bytes == appendix
    assert stored[2].content_bytes == generated
    assert stored[2].original_name == "Заявка на закупку REQ-1.docx"


@pytest.mark.parametrize("access", ["allowed", "read_only", "outside_scope", "contractor"])
def test_additional_source_is_private_and_requires_upload_permission_and_scope(
    test_client, set_current_user, set_uow, make_current_user, monkeypatch, access,
):
    uow = SourceUow()
    uow.requests.attach_hidden_file = AsyncMock()
    uow.requests.attach_file = AsyncMock()
    set_uow(uow)
    permissions = {PermissionCodes.REQUESTS_READ}
    if access != "read_only":
        permissions.add(PermissionCodes.REQUESTS_FILES_UPLOAD)
        permissions.add(PermissionCodes.REQUESTS_UPDATE)
    set_current_user(make_current_user(user_id="owner", role_id=3 if access == "contractor" else 6, permissions=permissions))
    monkeypatch.setattr(RequestService, "_resolve_visible_owner_ids_for_staff_scope",
                        AsyncMock(return_value=[] if access == "outside_scope" else ["owner"]))
    store = AsyncMock(return_value=SimpleNamespace(id=12))
    monkeypatch.setattr(FileService, "_store", store)
    public_event = AsyncMock()
    monkeypatch.setattr(RequestService, "_schedule_contractor_request_outbound", public_event)
    parse = Mock(side_effect=AssertionError("Additional hidden uploads must not run extraction"))
    monkeypatch.setattr(requests_api.RequestSpecificationService, "_parse", parse)
    document = Document()
    document.add_paragraph("Закрытое приложение без товарной таблицы")
    stream = io.BytesIO()
    document.save(stream)
    response = test_client.post("/api/v1/requests/REQ-1/source-files",
        files={"file": ("Приложение.docx", stream.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert response.status_code == (200 if access == "allowed" else 403), response.text
    if access == "allowed":
        uow.requests.attach_hidden_file.assert_awaited_once_with(request_id="REQ-1", file_id=12, is_specification_source=False)
        store.assert_awaited_once()
        assert response.json()["data"]["file_id"] == 12
    else:
        uow.requests.attach_hidden_file.assert_not_awaited()
        store.assert_not_awaited()
    uow.requests.attach_file.assert_not_awaited()
    public_event.assert_not_called()
    parse.assert_not_called()


@pytest.mark.parametrize("is_source", [True, False, None])
@pytest.mark.parametrize("access", ["allowed", "read_only", "outside_scope", "contractor"])
def test_hidden_file_deletion_checks_permission_scope_and_protects_sources(
    test_client, set_current_user, set_uow, make_current_user, monkeypatch, is_source, access,
):
    uow = SourceUow()
    uow.requests.list_hidden_files.return_value = [(SimpleNamespace(id=9, path="private", name="Файл.docx"), is_source)]
    uow.requests.get_hidden_file_for_update = AsyncMock(return_value=SimpleNamespace(is_specification_source=is_source))
    uow.requests.detach_hidden_file = AsyncMock(return_value=True)
    uow.files.count_links = AsyncMock(return_value=0)
    set_uow(uow)
    permissions = {PermissionCodes.REQUESTS_READ}
    if access != "read_only":
        permissions |= {PermissionCodes.REQUESTS_FILES_DELETE, PermissionCodes.REQUESTS_UPDATE}
    set_current_user(make_current_user(user_id="owner", role_id=3 if access == "contractor" else 6, permissions=permissions))
    monkeypatch.setattr(RequestService, "_resolve_visible_owner_ids_for_staff_scope",
                        AsyncMock(return_value=[] if access == "outside_scope" else ["owner"]))
    remove = AsyncMock()
    monkeypatch.setattr(FileService, "delete_file", remove)
    if access in {"allowed", "read_only"}:
        response = test_client.get("/api/v1/requests/REQ-1/source-files")
        assert response.status_code == 200
        assert response.json()["files"][0]["can_delete"] == (access == "allowed" and is_source is False)
    response = test_client.delete("/api/v1/requests/REQ-1/source-files/9")
    expected = 403 if access != "allowed" else (200 if is_source is False else 409)
    assert response.status_code == expected, response.text
    if expected == 200:
        uow.requests.detach_hidden_file.assert_awaited_once_with(request_id="REQ-1", file_id=9)
        remove.assert_awaited_once_with(file_id=9)
    else:
        uow.requests.detach_hidden_file.assert_not_awaited()
        remove.assert_not_awaited()


@pytest.mark.parametrize("scenario", ["other_request", "changed", "other_links"])
def test_hidden_file_delete_preserves_unrelated_links_and_handles_changes(
    test_client, set_current_user, set_uow, make_current_user, monkeypatch, scenario,
):
    uow = SourceUow()
    uow.requests.get_hidden_file_for_update = AsyncMock(return_value=None if scenario == "other_request" else SimpleNamespace(is_specification_source=False))
    uow.requests.detach_hidden_file = AsyncMock(return_value=scenario != "changed")
    uow.files.count_links = AsyncMock(return_value=1)
    set_uow(uow)
    set_current_user(make_current_user(user_id="owner", permissions={PermissionCodes.REQUESTS_READ, PermissionCodes.REQUESTS_FILES_DELETE, PermissionCodes.REQUESTS_UPDATE}))
    monkeypatch.setattr(RequestService, "_resolve_visible_owner_ids_for_staff_scope", AsyncMock(return_value=["owner"]))
    remove = AsyncMock()
    monkeypatch.setattr(FileService, "delete_file", remove)
    response = test_client.delete("/api/v1/requests/REQ-1/source-files/9")
    assert response.status_code == {"other_request": 404, "changed": 409, "other_links": 200}[scenario]
    remove.assert_not_awaited()
