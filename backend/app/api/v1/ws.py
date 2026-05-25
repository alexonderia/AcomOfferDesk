from __future__ import annotations

import asyncio
import time
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from pydantic import ValidationError
from starlette.websockets import WebSocketState

from app.api.dependencies import build_current_user_from_keycloak_claims
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.session_tokens import AccessTokenClaims
from app.core.uow import UnitOfWork
from app.domain.auth_context import CurrentUser as HttpCurrentUser
from app.domain.exceptions import Conflict, Forbidden, NotFound, Unauthorized
from app.domain.policies import CurrentUser, UserPolicy
from app.realtime.contracts import OutboundEnvelope, client_event_adapter
from app.realtime.runtime import ChatRealtimeRuntime, get_chat_runtime, get_unified_realtime_runtime
from app.services.identity_sync import IdentitySyncService
from app.services.keycloak_oidc import decode_keycloak_access_token, looks_like_keycloak_token
from app.services.ws_ticket_service import WsTicketPurpose, get_ws_ticket_service

router = APIRouter()


class CreateWsTicketRequest(BaseModel):
    purpose: str


class CreateWsTicketResponse(BaseModel):
    ticket: str
    expires_in: int
    expires_at: str


@router.post("/ws/tickets", response_model=CreateWsTicketResponse)
async def create_ws_ticket(
    payload: CreateWsTicketRequest,
    current_user: HttpCurrentUser = Depends(get_current_user),
) -> CreateWsTicketResponse:
    if payload.purpose not in {"chat_ws", "realtime_ws", "notifications_ws"}:
        raise HTTPException(status_code=400, detail="Неизвестное назначение websocket-билета")
    purpose: WsTicketPurpose = payload.purpose
    service = get_ws_ticket_service()
    raw_ticket, expires_at = await service.issue_ticket(
        user_id=current_user.user_id,
        role_id=current_user.role_id,
        status=current_user.status,
        keycloak_api_roles=current_user.keycloak_roles,
        purpose=purpose,
    )
    now = int(time.time())
    expires_ts = int(expires_at.timestamp())
    return CreateWsTicketResponse(
        ticket=raw_ticket,
        expires_in=max(0, expires_ts - now),
        expires_at=expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    )


async def _get_current_user_from_websocket(websocket: WebSocket) -> tuple[CurrentUser, AccessTokenClaims | None]:
    ticket = (websocket.query_params.get("ticket") or "").strip()
    if ticket:
        service = get_ws_ticket_service()
        access = await service.consume_ticket(raw_ticket=ticket, expected_purpose="chat_ws")
        UserPolicy.ensure_can_login(access.status)
        current_user = build_current_user_from_keycloak_claims(
            user_id=access.user_id,
            role_id=access.role_id,
            status=access.status,
            keycloak_api_roles=access.keycloak_api_roles,
        )
        return current_user, None

    if not settings.ws_legacy_query_token_enabled:
        raise Unauthorized("Необходимо войти в систему.")

    # TODO: remove legacy token query fallback after ws-ticket rollout stabilizes.
    token = (websocket.query_params.get("token") or "").strip()
    if not token:
        raise Unauthorized("Необходимо войти в систему.")

    if not looks_like_keycloak_token(token):
        raise Unauthorized("Необходимо войти в систему.")

    async with UnitOfWork() as uow:
        keycloak_claims = await decode_keycloak_access_token(token)
        sync_service = IdentitySyncService(
            users=uow.users,
            user_auth_accounts=uow.user_auth_accounts,
            user_contact_channels=uow.user_contact_channels,
            profiles=uow.profiles,
        )
        synced = await sync_service.sync_keycloak_identity(keycloak_claims, allow_user_creation=False)
        user = synced.user
        if user is None:
            raise Unauthorized("Не удалось подтвердить учетные данные.")
        claims = AccessTokenClaims(
            subject=user.id,
            issued_at=keycloak_claims.issued_at,
            expires_at=keycloak_claims.expires_at,
        )
        UserPolicy.ensure_can_login(user.status)
        current_user = build_current_user_from_keycloak_claims(
            user_id=user.id,
            role_id=user.id_role,
            status=user.status,
            keycloak_api_roles=keycloak_claims.api_roles,
        )
        return current_user, claims


async def _get_current_user_from_websocket_with_purpose(
    websocket: WebSocket,
    *,
    expected_purpose: WsTicketPurpose,
) -> tuple[CurrentUser, AccessTokenClaims | None]:
    ticket = (websocket.query_params.get("ticket") or "").strip()
    if ticket:
        service = get_ws_ticket_service()
        access = await service.consume_ticket(raw_ticket=ticket, expected_purpose=expected_purpose)
        UserPolicy.ensure_can_login(access.status)
        current_user = build_current_user_from_keycloak_claims(
            user_id=access.user_id,
            role_id=access.role_id,
            status=access.status,
            keycloak_api_roles=access.keycloak_api_roles,
        )
        return current_user, None

    if expected_purpose != "chat_ws":
        raise Unauthorized("Необходимо войти в систему.")

    return await _get_current_user_from_websocket(websocket)


async def _get_user_full_name(user_id: str) -> str | None:
    async with UnitOfWork() as uow:
        if uow.profiles is None:
            return None
        profile = await uow.profiles.get_by_id(user_id)
        return profile.full_name if profile else None


def _error_event(*, request_id: str | None, code: str, message: str) -> OutboundEnvelope:
    return OutboundEnvelope(
        type="error",
        request_id=request_id,
        data={
            "code": code,
            "message": message,
        },
    )


_REALTIME_EVENT_TYPES = (
    "connection.ready",
    "notification.created",
    "notification.read",
    "notification.read_all",
    "chat.message.created",
    "chat.message.delivered",
    "chat.message.read",
    "chat.typing.started",
    "chat.typing.stopped",
    "chat.sync",
    "error",
    "system.toast",
)

_WS_ERROR_TRANSLATIONS = {
    "Missing credentials": "Необходимо войти в систему.",
    "Invalid credentials": "Не удалось подтвердить учетные данные.",
    "Invalid websocket ticket": "Недействительный websocket-билет.",
    "Websocket ticket expired": "Срок действия websocket-билета истек.",
    "Invalid websocket ticket purpose": "Назначение websocket-билета не совпадает.",
    "Invalid payload": "Некорректные данные запроса.",
    "Message text cannot be empty": "Текст сообщения не может быть пустым.",
    "Invalid token payload": "Некорректные данные авторизации.",
    "Insufficient permissions to view chat": "Недостаточно прав для просмотра чата.",
    "Insufficient permissions to send chat message": "Недостаточно прав для отправки сообщения в чат.",
    "File not found": "Файл не найден.",
    "Message not found": "Сообщение не найдено.",
    "Notification not found": "Уведомление не найдено.",
}


def _build_chat_sync_payload(snapshot) -> dict:
    return {
        "chat_id": snapshot.chat_id,
        "last_message_id": snapshot.last_message_id,
        "last_read_message_id": snapshot.last_read_message_id,
        "last_read_at": snapshot.last_read_at.isoformat() if hasattr(snapshot.last_read_at, "isoformat") else snapshot.last_read_at,
        "is_muted": snapshot.is_muted,
        "is_archived": snapshot.is_archived,
        "resync_required": snapshot.resync_required,
    }


def _is_websocket_not_connected_error(exc: RuntimeError) -> bool:
    return "WebSocket is not connected" in str(exc)


def _translate_ws_error_message(message: str | None) -> str:
    normalized = (message or "").strip()
    if not normalized:
        return "Произошла ошибка. Попробуйте повторить действие."
    translated = _WS_ERROR_TRANSLATIONS.get(normalized)
    if translated is not None:
        return translated

    lowered = normalized.lower()
    if any(token in lowered for token in ("traceback", "stack trace", "sql", "rabbitmq", "smtp")):
        return "Произошла ошибка. Попробуйте повторить действие."
    if any(token in lowered for token in ("validationerror", "internal server error")):
        return "Произошла ошибка. Попробуйте повторить действие."
    if any("a" <= char.lower() <= "z" for char in normalized) and not any("а" <= char.lower() <= "я" or char in {"ё", "Ё"} for char in normalized):
        return "Произошла ошибка. Попробуйте повторить действие."
    return normalized


async def _run_chat_event_loop(
    *,
    websocket: WebSocket,
    runtime: ChatRealtimeRuntime,
    connection_id: str,
    current_user: CurrentUser,
) -> None:
    while True:
        if websocket.client_state is not WebSocketState.CONNECTED:
            break

        try:
            raw_event = await websocket.receive_json()
        except WebSocketDisconnect:
            break
        except RuntimeError as exc:
            if _is_websocket_not_connected_error(exc):
                break
            raise

        try:
            event = client_event_adapter.validate_python(raw_event)
        except ValidationError as exc:
            first_error = str(exc.errors()[0]["msg"]) if exc.errors() else "Invalid payload"
            await runtime.send_to_connection(
                connection_id=connection_id,
                event=_error_event(
                    request_id=raw_event.get("request_id") if isinstance(raw_event, dict) else None,
                    code="validation_error",
                    message=_translate_ws_error_message(first_error),
                ),
            )
            continue

        try:
            if event.type == "chat.subscribe":
                snapshot = await runtime.service.sync_chat(
                    current_user=current_user,
                    offer_id=event.data.chat_id,
                    last_known_message_id=None,
                )
                await runtime.manager.subscribe(connection_id=connection_id, chat_id=event.data.chat_id)
                if snapshot.last_message_id is not None:
                    delivered = await runtime.service.mark_delivered_for_online_user(
                        offer_id=event.data.chat_id,
                        user_id=current_user.user_id,
                        up_to_message_id=snapshot.last_message_id,
                    )
                    if delivered.updated_message_ids:
                        await runtime.publish_chat_event(
                            chat_id=event.data.chat_id,
                            event=OutboundEnvelope(
                                type="message.delivered",
                                data={
                                    "chat_id": event.data.chat_id,
                                    "user_id": current_user.user_id,
                                    "message_ids": delivered.updated_message_ids,
                                },
                            ),
                        )

                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=OutboundEnvelope(
                        type="ack",
                        request_id=event.request_id,
                        data={
                            "event_type": event.type,
                            "chat_id": event.data.chat_id,
                        },
                    ),
                )
                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=OutboundEnvelope(
                        type="chat.sync",
                        request_id=event.request_id,
                        data=_build_chat_sync_payload(snapshot),
                    ),
                )
                continue

            if event.type == "chat.unsubscribe":
                await runtime.manager.unsubscribe(connection_id=connection_id, chat_id=event.data.chat_id)
                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=OutboundEnvelope(
                        type="chat.unsubscribed",
                        request_id=event.request_id,
                        data={"chat_id": event.data.chat_id},
                    ),
                )
                continue

            if event.type == "message.send":
                result, message_payload = await runtime.service.create_message(
                    current_user=current_user,
                    offer_id=event.data.chat_id,
                    text=event.data.text,
                    file_refs=[file_ref.model_dump(mode="python") for file_ref in event.data.files],
                )
                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=OutboundEnvelope(
                        type="ack",
                        request_id=event.request_id,
                        data={
                            "event_type": event.type,
                            "chat_id": result.chat_id,
                            "message_id": result.message_id,
                        },
                    ),
                )
                await runtime.publish_chat_event(
                    chat_id=result.chat_id,
                    event=OutboundEnvelope(
                        type="message.created",
                        request_id=event.request_id,
                        data=message_payload,
                    ),
                )
                continue

            if event.type == "message.read":
                ack = await runtime.service.mark_read(
                    current_user=current_user,
                    offer_id=event.data.chat_id,
                    message_ids=event.data.message_ids,
                    up_to_message_id=event.data.up_to_message_id,
                )
                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=OutboundEnvelope(
                        type="ack",
                        request_id=event.request_id,
                        data={
                            "event_type": event.type,
                            "chat_id": ack.chat_id,
                            "updated_count": ack.updated_count,
                            "last_read_message_id": ack.last_read_message_id,
                        },
                    ),
                )
                if ack.updated_message_ids:
                    user_full_name = await _get_user_full_name(current_user.user_id)
                    await runtime.publish_chat_event(
                        chat_id=ack.chat_id,
                        event=OutboundEnvelope(
                            type="message.read",
                            data={
                                "chat_id": ack.chat_id,
                                "user_id": current_user.user_id,
                                "user_full_name": user_full_name,
                                "message_ids": ack.updated_message_ids,
                                "last_read_message_id": ack.last_read_message_id,
                            },
                        ),
                    )
                continue

            if event.type in {"typing.start", "typing.stop"}:
                await runtime.publish_chat_event(
                    chat_id=event.data.chat_id,
                    exclude_user_ids={current_user.user_id},
                    event=OutboundEnvelope(
                        type=event.type,
                        data={
                            "chat_id": event.data.chat_id,
                            "user_id": current_user.user_id,
                        },
                    ),
                )
                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=OutboundEnvelope(
                        type="ack",
                        request_id=event.request_id,
                        data={
                            "event_type": event.type,
                            "chat_id": event.data.chat_id,
                        },
                    ),
                )
                continue

            if event.type == "chat.sync":
                snapshot = await runtime.service.sync_chat(
                    current_user=current_user,
                    offer_id=event.data.chat_id,
                    last_known_message_id=event.data.last_known_message_id,
                )
                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=OutboundEnvelope(
                        type="chat.sync",
                        request_id=event.request_id,
                        data=_build_chat_sync_payload(snapshot),
                    ),
                )
        except (Conflict, Forbidden, NotFound, Unauthorized) as exc:
            await runtime.send_to_connection(
                connection_id=connection_id,
                event=_error_event(
                    request_id=event.request_id,
                    code=exc.__class__.__name__.lower(),
                    message=_translate_ws_error_message(str(exc)),
                ),
            )


@router.websocket("/ws/realtime")
async def unified_realtime_websocket(websocket: WebSocket) -> None:
    try:
        current_user, _claims = await _get_current_user_from_websocket_with_purpose(
            websocket,
            expected_purpose="realtime_ws",
        )
    except (Conflict, Forbidden, Unauthorized):
        await websocket.close(code=4401)
        return

    chat_runtime = get_chat_runtime()
    runtime = get_unified_realtime_runtime()
    connection_id = await runtime.connect(websocket=websocket, user_id=current_user.user_id)
    try:
        await runtime.manager.send_to_connection(
            connection_id=connection_id,
            event=OutboundEnvelope(
                type="connection.ready",
                data={
                    "connection_id": connection_id,
                    "user_id": current_user.user_id,
                    "transport": "websocket",
                    "supported_event_types": list(_REALTIME_EVENT_TYPES),
                },
            ),
        )
        await _run_chat_event_loop(
            websocket=websocket,
            runtime=chat_runtime,
            connection_id=connection_id,
            current_user=current_user,
        )
    finally:
        await runtime.disconnect(connection_id=connection_id)


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket) -> None:
    try:
        current_user, claims = await _get_current_user_from_websocket_with_purpose(
            websocket,
            expected_purpose="chat_ws",
        )
    except (Conflict, Forbidden, Unauthorized):
        await websocket.close(code=4401)
        return

    runtime = get_chat_runtime()
    connection_id = await runtime.manager.connect(websocket=websocket, user_id=current_user.user_id)
    expiry_task: asyncio.Task[None] | None = None

    async def close_on_expiry() -> None:
        if claims is None:
            return
        delay = max(0, claims.expires_at - int(time.time()))
        try:
            await asyncio.sleep(delay)
            await websocket.close(code=4401)
        except Exception:
            return

    expiry_task = asyncio.create_task(close_on_expiry())
    await runtime.send_to_connection(
        connection_id=connection_id,
        event=OutboundEnvelope(
            type="connection.ready",
            data={
                "connection_id": connection_id,
                "user_id": current_user.user_id,
                "transport": "websocket",
            },
        ),
    )

    try:
        await _run_chat_event_loop(
            websocket=websocket,
            runtime=runtime,
            connection_id=connection_id,
            current_user=current_user,
        )
    except WebSocketDisconnect:
        pass
    finally:
        if expiry_task is not None:
            expiry_task.cancel()
        await runtime.manager.disconnect(connection_id)
