from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from starlette.websockets import WebSocketState

from app.core.session_tokens import AccessTokenClaims
from app.core.uow import UnitOfWork
from app.domain.auth_context import build_current_user
from app.domain.exceptions import Conflict, Forbidden, NotFound, Unauthorized
from app.domain.policies import CurrentUser, UserPolicy
from app.realtime.contracts import OutboundEnvelope, client_event_adapter
from app.realtime.runtime import get_chat_runtime
from app.services.identity_sync import IdentitySyncService
from app.services.keycloak_oidc import decode_keycloak_access_token, looks_like_keycloak_token

router = APIRouter()


async def _get_current_user_from_websocket(websocket: WebSocket) -> tuple[CurrentUser, AccessTokenClaims]:
    token = (websocket.query_params.get("token") or "").strip()
    if not token:
        raise Unauthorized("Missing credentials")

    if not looks_like_keycloak_token(token):
        raise Unauthorized("Missing credentials")

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
        claims = AccessTokenClaims(
            subject=user.id,
            issued_at=keycloak_claims.issued_at,
            expires_at=keycloak_claims.expires_at,
        )
        if user is None:
            raise Unauthorized("Invalid credentials")
        UserPolicy.ensure_can_login(user.status)
        return build_current_user(user_id=user.id, role_id=user.id_role, status=user.status), claims


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


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket) -> None:
    try:
        current_user, claims = await _get_current_user_from_websocket(websocket)
    except (Conflict, Forbidden, Unauthorized):
        await websocket.close(code=4401)
        return

    runtime = get_chat_runtime()
    connection_id = await runtime.manager.connect(websocket=websocket, user_id=current_user.user_id)
    expiry_task: asyncio.Task[None] | None = None

    async def close_on_expiry() -> None:
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
        while True:
            if websocket.client_state is not WebSocketState.CONNECTED:
                break

            try:
                raw_event = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except RuntimeError as exc:
                if "WebSocket is not connected" in str(exc):
                    break
                raise

            try:
                event = client_event_adapter.validate_python(raw_event)
            except ValidationError as exc:
                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=_error_event(
                        request_id=raw_event.get("request_id") if isinstance(raw_event, dict) else None,
                        code="validation_error",
                        message=str(exc.errors()[0]["msg"]) if exc.errors() else "Invalid payload",
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
                            data={
                                "chat_id": snapshot.chat_id,
                                "last_message_id": snapshot.last_message_id,
                                "last_read_message_id": snapshot.last_read_message_id,
                                "last_read_at": snapshot.last_read_at.isoformat() if hasattr(snapshot.last_read_at, "isoformat") else snapshot.last_read_at,
                                "is_muted": snapshot.is_muted,
                                "is_archived": snapshot.is_archived,
                                "resync_required": snapshot.resync_required,
                            },
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
                            data={
                                "chat_id": snapshot.chat_id,
                                "last_message_id": snapshot.last_message_id,
                                "last_read_message_id": snapshot.last_read_message_id,
                                "last_read_at": snapshot.last_read_at.isoformat() if hasattr(snapshot.last_read_at, "isoformat") else snapshot.last_read_at,
                                "is_muted": snapshot.is_muted,
                                "is_archived": snapshot.is_archived,
                                "resync_required": snapshot.resync_required,
                            },
                        ),
                    )
            except (Conflict, Forbidden, NotFound, Unauthorized) as exc:
                await runtime.send_to_connection(
                    connection_id=connection_id,
                    event=_error_event(
                        request_id=event.request_id,
                        code=exc.__class__.__name__.lower(),
                        message=str(exc),
                    ),
                )
    except WebSocketDisconnect:
        pass
    finally:
        if expiry_task is not None:
            expiry_task.cancel()
        await runtime.manager.disconnect(connection_id)
