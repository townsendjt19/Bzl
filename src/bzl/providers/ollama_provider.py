import json
from collections.abc import AsyncIterator

import httpx

from bzl.models.provider import ProviderMessage, ProviderResponse


def _build_messages(
    context: list[ProviderMessage] | None, message: str
) -> list[dict[str, str]]:
    history = [{"role": m.role, "content": m.content} for m in (context or [])]
    history.append({"role": "user", "content": message})
    return history


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "llama3",
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.host = host
        self.model = model
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self._transport, timeout=30)

    async def send_message(
        self, message: str, *, context: list[ProviderMessage] | None = None
    ) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": _build_messages(context, message),
            "stream": False,
        }
        try:
            async with self._client() as client:
                response = await client.post(f"{self.host}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            return ProviderResponse(
                content=f"ollama request failed: {exc}", provider=self.name, stub=False
            )
        content = data.get("message", {}).get("content", "")
        return ProviderResponse(content=content, provider=self.name, stub=False)

    async def stream_response(
        self, message: str, *, context: list[ProviderMessage] | None = None
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": _build_messages(context, message),
            "stream": True,
        }
        try:
            async with self._client() as client:
                async with client.stream("POST", f"{self.host}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        piece = chunk.get("message", {}).get("content", "")
                        if piece:
                            yield piece
        except httpx.HTTPError as exc:
            yield f"ollama request failed: {exc}"
