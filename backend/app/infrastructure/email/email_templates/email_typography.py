from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from urllib.parse import quote

from app.core.config import settings


@lru_cache(maxsize=1)
def _font_styles() -> str:
    return files("shared").joinpath("fonts", "alabuga-sans.css").read_text(encoding="utf-8")


def build_email_font_head() -> str:
    """Use the portal's bundled font in mail clients that support web fonts."""
    public_base = settings.web_base_url or settings.public_backend_base_url
    font_faces = ""
    if public_base:
        # Percent-encode CSS delimiters as well as non-ASCII URL characters.
        font_base = quote(public_base.rstrip("/"), safe=":/[]%")
        font_faces = _font_styles().replace("url('./", f"url('{font_base}/maintenance-assets/fonts/")
    return (
        '<head><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<style>{font_faces}"
        "body,table,td,a,p,span{font-family:'Alabuga Sans',sans-serif}"
        "body{overflow-wrap:anywhere}"
        '@media(max-width:480px){'
        'table[width="600"]>tbody>tr>td{padding-left:12px!important;padding-right:12px!important}'
        'table[width="600"]>tbody>tr:first-child>td{font-size:18px!important}}'
        "</style></head>"
    )
