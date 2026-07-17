import httpx
import pytest

from app.infrastructure.gemini import GeminiClient


class FailingClient:
    async def __aenter__(self) -> "FailingClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(self, *args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("POST", "https://example.test")
        return httpx.Response(503, request=request)


@pytest.mark.asyncio
async def test_gemini_503_has_retryable_message(monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("app.infrastructure.gemini.httpx.AsyncClient", lambda **_: FailingClient())
    monkeypatch.setattr("app.infrastructure.gemini.asyncio.sleep", no_sleep)
    client = GeminiClient("test-key", "gemini-flash-latest", "gemini-embedding-001")

    with pytest.raises(RuntimeError, match="temporarily unavailable"):
        await client.embed_query("test")
