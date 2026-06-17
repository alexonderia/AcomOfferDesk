import pytest

from app.infrastructure.email.reply_token_codec import ReplyTokenCodec


@pytest.mark.asyncio
async def test_parse_token_keeps_text_request_id() -> None:
    codec = ReplyTokenCodec(secret="reply-secret")

    token = await codec.create_token(request_id="333", user_id="contractor-1", ttl_seconds=300)
    claims = await codec.parse_token(token)

    assert claims.request_id == "333"
    assert isinstance(claims.request_id, str)
    assert claims.user_id == "contractor-1"
