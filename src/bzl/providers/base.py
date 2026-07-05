from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol, runtime_checkable

from bzl.models.provider import ProviderMessage, ProviderResponse


@runtime_checkable
class AIProvider(Protocol):
    """Pure async interface for an AI provider. No dependency on services or UI."""

    name: str

    async def send_message(
        self,
        message: str,
        *,
        context: list[ProviderMessage] | None = None,
        cwd: Path | None = None,
    ) -> ProviderResponse: ...

    def stream_response(
        self,
        message: str,
        *,
        context: list[ProviderMessage] | None = None,
        cwd: Path | None = None,
    ) -> AsyncIterator[str]: ...
