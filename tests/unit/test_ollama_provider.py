import json

import httpx

from bzl.models.provider import ProviderMessage
from bzl.providers.ollama_provider import OllamaProvider


def _handler(response_json=None, status_code=200, raise_error=False):
    def handler(request: httpx.Request) -> httpx.Response:
        if raise_error:
            raise httpx.ConnectError("connection refused", request=request)
        payload = json.loads(request.content)
        if payload["stream"]:
            lines = "\n".join(
                json.dumps({"message": {"content": chunk}}) for chunk in ["hel", "lo"]
            )
            return httpx.Response(status_code, text=lines)
        return httpx.Response(status_code, json=response_json)

    return handler


async def test_send_message_returns_content():
    handler = _handler({"message": {"content": "hi"}})
    provider = OllamaProvider(transport=httpx.MockTransport(handler))
    response = await provider.send_message("hello")
    assert response.content == "hi"
    assert response.provider == "ollama"
    assert response.stub is False


async def test_send_message_includes_history_in_request():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": "ok"}})

    provider = OllamaProvider(transport=httpx.MockTransport(handler))
    context = [ProviderMessage(role="user", content="earlier")]
    await provider.send_message("hello", context=context)

    messages = captured["payload"]["messages"]
    assert messages[0] == {"role": "user", "content": "earlier"}
    assert messages[-1] == {"role": "user", "content": "hello"}


async def test_send_message_reports_connection_error():
    provider = OllamaProvider(transport=httpx.MockTransport(_handler(raise_error=True)))
    response = await provider.send_message("hello")
    assert "ollama request failed" in response.content
    assert response.stub is False


async def test_stream_response_yields_chunks():
    provider = OllamaProvider(transport=httpx.MockTransport(_handler()))
    chunks = [chunk async for chunk in provider.stream_response("hello")]
    assert chunks == ["hel", "lo"]


async def test_stream_response_reports_connection_error():
    provider = OllamaProvider(transport=httpx.MockTransport(_handler(raise_error=True)))
    chunks = [chunk async for chunk in provider.stream_response("hello")]
    assert len(chunks) == 1
    assert "ollama request failed" in chunks[0]
