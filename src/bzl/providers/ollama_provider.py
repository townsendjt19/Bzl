import asyncio
from collections.abc import AsyncIterator

from bzl.models.provider import ProviderMessage, ProviderResponse


class OllamaProvider:
    name = "ollama"

    async def send_message(
        self, message: str, *, context: list[ProviderMessage] | None = None
    ) -> ProviderResponse:
        return ProviderResponse(
            content=f"[stub:{self.name}] received: {message}", provider=self.name, stub=True
        )

    async def stream_response(
        self, message: str, *, context: list[ProviderMessage] | None = None
    ) -> AsyncIterator[str]:
        for chunk in (f"[stub:{self.name}] ", "streaming ", "response"):
            await asyncio.sleep(0)
            yield chunk
