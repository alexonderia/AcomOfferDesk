from __future__ import annotations

import base64
import html
import secrets
from functools import lru_cache
from pathlib import Path

from fastapi.responses import HTMLResponse


_STATIC_DIR = Path(__file__).resolve().parent / "static"
_BITRIX_URL = (
    "https://team.alabuga.ru/company/structure.php"
    "?set_filter_structure=Y&structure_UF_DEPARTMENT=8304&filter=Y&set_filter=Y"
)
_MAX_URL = "https://max.ru/u/f9LHodD0cOIA4s2RhH3dW5NoCLRn88NF67UYfQe_rOnnM6Y1a7VW_vOUt5I"
_EYE_ICON = (
    '<svg class="aod-icon-eye" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M2.5 12s3.6-7 9.5-7 9.5 7 9.5 7-3.6 7-9.5 7-9.5-7-9.5-7Z"/>'
    '<circle cx="12" cy="12" r="3"/></svg>'
)
_EYE_OFF_ICON = (
    '<svg class="aod-icon-eye-off" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M3 3l18 18"/>'
    '<path d="M10.6 10.6A3 3 0 0 0 12 15a3 3 0 0 0 2.4-4.4"/>'
    '<path d="M6.5 6.7C4.2 8.3 2.5 12 2.5 12s3.6 7 9.5 7c2 0 3.7-.6 5.1-1.5"/>'
    '<path d="M14.1 6.3A10.5 10.5 0 0 1 12 5c-5.9 0-9.5 7-9.5 7"/>'
    '<path d="M17.6 9.3C19.6 10.8 21.5 12 21.5 12s-3.6 7-9.5 7"/></svg>'
)
_PASSWORD_TOGGLE_SCRIPT = """
document.querySelectorAll("[data-password-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const field = button.closest(".aod-password");
    const input = field && field.querySelector("input");
    if (!input) {
      return;
    }
    const hidden = input.type === "password";
    input.type = hidden ? "text" : "password";
    button.setAttribute("aria-pressed", hidden ? "true" : "false");
    button.setAttribute("aria-label", hidden ? "Скрыть пароль" : "Показать пароль");
  });
});
"""
def _page_csp(script_nonce: str) -> str:
    return (
        "default-src 'none'; style-src 'unsafe-inline'; "
        f"script-src 'nonce-{script_nonce}'; img-src data:; "
        "form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )
_PAGE_STYLE = """
:root {
  --aod-primary: #2f6fd6;
  --aod-primary-dark: #245bb5;
  --aod-bg: #edf3ff;
  --aod-surface: #ffffff;
  --aod-text: #1f2a44;
  --aod-text-muted: #4a5875;
  --aod-border: #d3dbe7;
  --aod-shadow: 0 12px 28px rgba(15, 35, 75, 0.08);
  --aod-control-radius: 36px;
}
*, *::before, *::after { box-sizing: border-box; }
html, body {
  min-height: 100%;
  margin: 0;
  font-family: Inter, "Segoe UI", sans-serif;
  font-size: 16px;
  color: var(--aod-text);
  -webkit-font-smoothing: antialiased;
}
.aod-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at top right, rgba(47, 111, 214, 0.08), transparent 30%),
    radial-gradient(circle at bottom left, rgba(47, 111, 214, 0.06), transparent 34%),
    var(--aod-bg);
}
.aod-shell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.aod-card {
  width: min(460px, 94vw);
  border-radius: 20px;
  border: 1px solid var(--aod-border);
  background: var(--aod-surface);
  box-shadow: var(--aod-shadow);
  padding: 32px;
}
.aod-card__header { margin-bottom: 12px; text-align: center; }
.aod-card__title {
  margin: 0;
  font-size: 20px;
  line-height: 1.25;
  font-weight: 700;
  color: var(--aod-text);
}
.aod-card__body { display: grid; gap: 16px; }
.aod-card form { display: grid; gap: 18px; }
.aod-field { display: grid; gap: 8px; }
label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: var(--aod-text);
}
input {
  width: 100%;
  min-height: 56px;
  padding: 14px 16px;
  border: 1px solid var(--aod-border);
  border-radius: var(--aod-control-radius);
  background: var(--aod-surface);
  color: var(--aod-text);
  font: inherit;
  outline: none;
  box-shadow: none;
}
input:hover { border-color: #bcc7da; }
input:focus { border-color: #aeb9cc; }
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
  -webkit-box-shadow: 0 0 0 1000px var(--aod-surface) inset;
  box-shadow: 0 0 0 1000px var(--aod-surface) inset;
  -webkit-text-fill-color: var(--aod-text);
}
.aod-password {
  position: relative;
  display: flex;
  align-items: center;
}
.aod-password input { padding-right: 52px; }
.aod-password-toggle {
  position: absolute;
  right: 8px;
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: #f5f8ff;
  color: var(--aod-text-muted);
  cursor: pointer;
}
.aod-password-toggle:hover { background: #ebf2ff; color: var(--aod-text); }
.aod-password-toggle svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.aod-password-toggle[aria-pressed="false"] .aod-icon-eye-off { display: none; }
.aod-password-toggle[aria-pressed="true"] .aod-icon-eye { display: none; }
.aod-form-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
.aod-button,
.aod-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 48px;
  margin: 0;
  padding: 0 20px;
  border: 0;
  border-radius: var(--aod-control-radius);
  background: var(--aod-primary);
  color: #fff;
  font: inherit;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}
.aod-button:hover, .aod-action:hover { background: var(--aod-primary-dark); }
.aod-plain-link {
  display: inline-flex;
  align-self: center;
  justify-content: center;
  width: auto;
  margin: 0;
  padding: 0;
  color: var(--aod-primary);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
}
.aod-plain-link:hover { color: var(--aod-primary-dark); text-decoration: underline; }
.aod-alert {
  margin: 0;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(198, 63, 63, 0.28);
  background: #fff5f5;
  color: #c63f3f;
  font-size: 14px;
  line-height: 1.55;
}
.aod-hint {
  margin: 0;
  color: var(--aod-text-muted);
  font-size: 14px;
  line-height: 1.55;
}
.aod-app-footer {
  width: 100%;
  padding: 6px 20px 18px;
}
.aod-app-footer__panel {
  max-width: 1200px;
  margin: 0 auto;
  padding: 8px 14px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 4px 14px rgba(15, 35, 75, 0.06);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}
.aod-app-footer__section {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.aod-app-footer__section--start { justify-self: start; }
.aod-app-footer__section--end { justify-self: end; }
.aod-app-footer__text {
  color: var(--aod-text-muted);
  font-size: 12px;
  font-weight: 500;
}
.aod-app-footer__brand {
  text-align: center;
  font-size: 14px;
  font-weight: 550;
  letter-spacing: 0.1px;
  color: var(--aod-text);
  white-space: nowrap;
}
.aod-app-footer__icon-link {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  border: 1px solid var(--aod-border);
  background: rgba(255, 255, 255, 0.86);
}
.aod-app-footer__icon-link img {
  width: 24px;
  height: 24px;
  object-fit: cover;
  border-radius: 16px;
}
@media (max-width: 640px) {
  .aod-shell { align-items: flex-start; padding: 16px; }
  .aod-card { width: 100%; padding: 24px 20px 20px; border-radius: 18px; }
  .aod-app-footer { padding: 0 12px 12px; }
  .aod-app-footer__panel {
    grid-template-columns: 1fr;
    padding: 10px 12px;
    border-radius: 22px;
    text-align: center;
  }
  .aod-app-footer__section,
  .aod-app-footer__section--start,
  .aod-app-footer__section--end { justify-self: center; }
}
"""


@lru_cache(maxsize=None)
def _logo_data_uri(filename: str) -> str:
    payload = (_STATIC_DIR / filename).read_bytes()
    encoded = base64.standard_b64encode(payload).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _password_input_html(
    *,
    field_id: str,
    name: str,
    autocomplete: str,
    max_length: int = 128,
    min_length: int | None = None,
) -> str:
    extra_attrs = f'maxlength="{max_length}" required'
    if min_length is not None:
        extra_attrs = f'minlength="{min_length}" {extra_attrs}'
    safe_id = html.escape(field_id, quote=True)
    return (
        f'<div class="aod-password">'
        f'<input id="{safe_id}" name="{html.escape(name, quote=True)}" type="password" '
        f'autocomplete="{html.escape(autocomplete, quote=True)}" {extra_attrs}>'
        '<button class="aod-password-toggle" type="button" data-password-toggle '
        'aria-label="Показать пароль" aria-pressed="false">'
        f"{_EYE_ICON}{_EYE_OFF_ICON}</button></div>"
    )


def _footer_html() -> str:
    bitrix_src = html.escape(_logo_data_uri("bitrix24-logo.png"), quote=True)
    max_src = html.escape(_logo_data_uri("max-logo-2025.png"), quote=True)
    bitrix_link = (
        f'<a class="aod-app-footer__icon-link" href="{html.escape(_BITRIX_URL, quote=True)}" '
        'target="_blank" rel="noreferrer" aria-label="Перейти в Битрикс">'
        f'<img src="{bitrix_src}" alt="Bitrix24"></a>'
    )
    max_link = (
        f'<a class="aod-app-footer__icon-link" href="{html.escape(_MAX_URL, quote=True)}" '
        'target="_blank" rel="noreferrer" aria-label="Открыть MAX">'
        f'<img src="{max_src}" alt="MAX"></a>'
    )
    return (
        '<footer class="aod-app-footer"><div class="aod-app-footer__panel">'
        '<div class="aod-app-footer__section aod-app-footer__section--start">'
        '<span class="aod-app-footer__text">Created by «Цифровизация проектных задач»</span>'
        f"{bitrix_link}</div>"
        '<div class="aod-app-footer__brand">AcomOfferDesk</div>'
        '<div class="aod-app-footer__section aod-app-footer__section--end">'
        '<span class="aod-app-footer__text">По вопросам системы писать сюда</span>'
        f"{max_link}</div>"
        "</div></footer>"
    )


def render_browser_page(*, title: str, body: str, status_code: int = 200) -> HTMLResponse:
    script_nonce = secrets.token_urlsafe(18)
    response = HTMLResponse(
        "<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>"
        f"<style>{_PAGE_STYLE}</style></head>"
        '<body><div class="aod-page"><main class="aod-shell">'
        f'<section class="aod-card" aria-label="{html.escape(title, quote=True)}">'
        f"{body}"
        f"</section></main>{_footer_html()}</div>"
        f'<script nonce="{html.escape(script_nonce, quote=True)}">{_PASSWORD_TOGGLE_SCRIPT}</script>'
        "</body></html>",
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": _page_csp(script_nonce),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )
    response.status_code = status_code
    return response


def render_login_page(*, error: str | None = None, status_code: int = 200) -> HTMLResponse:
    error_html = f'<p class="aod-alert">{html.escape(error)}</p>' if error else ""
    return render_browser_page(
        title="Вход в AcomOfferDesk",
        status_code=status_code,
        body=(
            '<div class="aod-card__header"><h1 class="aod-card__title">Вход в AcomOfferDesk</h1></div>'
            '<div class="aod-card__body">'
            f"{error_html}"
            '<form method="post" action="/iam/login" autocomplete="on">'
            '<div class="aod-field"><label for="login">Логин или email</label>'
            '<input id="login" name="login" autocomplete="username" maxlength="128" required></div>'
            '<div class="aod-field"><label for="password">Пароль</label>'
            f'{_password_input_html(field_id="password", name="password", autocomplete="current-password")}</div>'
            '<div class="aod-form-toolbar">'
            '<a class="aod-plain-link" href="/login?reset=1">Восстановить доступ</a>'
            "</div>"
            '<button class="aod-button" type="submit">Войти</button>'
            "</form></div>"
        ),
    )


def render_login_restart_page(*, error: str, status_code: int = 400) -> HTMLResponse:
    return render_browser_page(
        title="Вход в AcomOfferDesk",
        status_code=status_code,
        body=(
            '<div class="aod-card__header"><h1 class="aod-card__title">Вход в AcomOfferDesk</h1></div>'
            '<div class="aod-card__body">'
            f'<p class="aod-alert">{html.escape(error)}</p>'
            '<p class="aod-hint">Начните вход заново, чтобы создать новую защищённую сессию.</p>'
            '<a class="aod-action" href="/api/v1/auth/login">Войти снова</a>'
            "</div>"
        ),
    )


def render_password_page(*, purpose: str, token: str, error: str | None = None) -> HTMLResponse:
    title = "Создание пароля" if purpose == "password_setup" else "Новый пароль"
    path = "setup" if purpose == "password_setup" else "reset"
    error_html = f'<p class="aod-alert">{html.escape(error)}</p>' if error else ""
    return render_browser_page(
        title=title,
        body=(
            f'<div class="aod-card__header"><h1 class="aod-card__title">{title}</h1></div>'
            '<div class="aod-card__body">'
            f"{error_html}"
            f'<form method="post" action="/iam/password/{path}">'
            f'<input type="hidden" name="token" value="{html.escape(token, quote=True)}">'
            '<div class="aod-field"><label for="new_password">Пароль</label>'
            f'{_password_input_html(field_id="new_password", name="new_password", autocomplete="new-password", min_length=12)}</div>'
            '<div class="aod-field"><label for="password_confirmation">Повторите пароль</label>'
            f'{_password_input_html(field_id="password_confirmation", name="password_confirmation", autocomplete="new-password", min_length=12)}</div>'
            '<p class="aod-hint">Используйте не менее 12 символов.</p>'
            f'<button class="aod-button" type="submit">{title}</button></form></div>'
        ),
    )


def render_password_saved_page(*, purpose: str) -> HTMLResponse:
    hint = (
        "Пароль создан. Если учётная запись активна, теперь можно войти."
        if purpose == "password_setup"
        else "Теперь можно вернуться в AcomOfferDesk и войти с новым паролем."
    )
    return render_browser_page(
        title="Пароль сохранён",
        body=(
            '<div class="aod-card__header"><h1 class="aod-card__title">Пароль сохранён</h1></div>'
            '<div class="aod-card__body">'
            f'<p class="aod-hint">{hint}</p>'
            '<a class="aod-action" href="/login">Войти</a>'
            "</div>"
        ),
    )
