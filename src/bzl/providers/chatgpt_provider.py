import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from bzl.models.provider import ProviderMessage, ProviderResponse


class ChatGPTProvider:
    name = "chatgpt"

    async def send_message(
        self,
        message: str,
        *,
        context: list[ProviderMessage] | None = None,
        cwd: Path | None = None,
    ) -> ProviderResponse:
        return ProviderResponse(
            content=f"[stub:{self.name}] received: {message}", provider=self.name, stub=True
        )

    async def stream_response(
        self,
        message: str,
        *,
        context: list[ProviderMessage] | None = None,
        cwd: Path | None = None,
    ) -> AsyncIterator[str]:
        for chunk in (f"[stub:{self.name}] ", "streaming ", "response"):
            await asyncio.sleep(0)
            yield chunk
