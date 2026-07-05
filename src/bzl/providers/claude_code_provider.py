import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable

from bzl.models.provider import ProviderMessage, ProviderResponse

SubprocessRunner = Callable[..., Awaitable["asyncio.subprocess.Process"]]


def _build_prompt(context: list[ProviderMessage] | None, message: str) -> str:
    if not context:
        return message
    transcript = "\n".join(f"{m.role}: {m.content}" for m in context)
    return f"{transcript}\nuser: {message}"


class ClaudeCodeProvider:
    name = "claude_code"

    def __init__(
        self,
        command: str = "claude",
        *,
        run_subprocess: SubprocessRunner = asyncio.create_subprocess_exec,
    ) -> None:
        self.command = command
        self._run_subprocess = run_subprocess

    async def send_message(
        self, message: str, *, context: list[ProviderMessage] | None = None
    ) -> ProviderResponse:
        prompt = _build_prompt(context, message)
        try:
            process = await self._run_subprocess(
                self.command,
                "-p",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
        except FileNotFoundError:
            return ProviderResponse(
                content=f"{self.command!r} CLI not found on PATH", provider=self.name, stub=False
            )
        if process.returncode != 0:
            return ProviderResponse(
                content=f"claude error: {stderr.decode().strip()}", provider=self.name, stub=False
            )
        return ProviderResponse(content=stdout.decode().strip(), provider=self.name, stub=False)

    async def stream_response(
        self, message: str, *, context: list[ProviderMessage] | None = None
    ) -> AsyncIterator[str]:
        response = await self.send_message(message, context=context)
        yield response.content
