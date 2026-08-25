from __future__ import annotations

import logging
from typing import Literal
from urllib.parse import quote

from app.core.config import settings
from app.infrastructure.email.email_templates.iam_password_setup_email import (
    build_iam_password_setup_email,
)
from app.infrastructure.email.sensitive_email_service import SensitiveEmailService


logger = logging.getLogger(__name__)
PasswordActionPurpose = Literal["password_setup", "password_reset"]


async def send_iam_password_action_email(
    *,
    to_email: str,
    raw_token: str,
    purpose: PasswordActionPurpose,
) -> None:
    path = "setup" if purpose == "password_setup" else "reset"
    action_url = f"{settings.iam_bff_auth_base_url}/password/{path}?token={quote(raw_token, safe='')}"
    payload = build_iam_password_setup_email(
        setup_url=action_url,
        is_reset=purpose == "password_reset",
    )
    email_service = SensitiveEmailService(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_security=settings.smtp_security,
        username=settings.email_address,
        password=settings.email_app_password,
        from_address=settings.email_address,
        from_name=settings.email_from_name,
    )
    await email_service.send_email(
        to_email=to_email,
        subject=payload.subject,
        text_content=payload.text_content,
        html_content=payload.html_content,
    )


async def send_iam_password_action_email_safely(
    *,
    to_email: str,
    raw_token: str,
    purpose: PasswordActionPurpose,
) -> None:
    """Preserve the generic reset response when direct SMTP delivery fails."""

    try:
        await send_iam_password_action_email(
            to_email=to_email,
            raw_token=raw_token,
            purpose=purpose,
        )
    except Exception as exc:
        logger.error(
            "iam_password_action_delivery_failed purpose=%s exception_type=%s",
            purpose,
            type(exc).__name__,
        )
