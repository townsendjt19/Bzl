from bzl.models.provider import ProviderMessage
from bzl.providers.claude_code_provider import ClaudeCodeProvider


class FakeProcess:
    def __init__(self, stdout: bytes, stderr: bytes, returncode: int) -> None:
        self.stdout_bytes = stdout
        self.stderr_bytes = stderr
        self.returncode = returncode

    async def communicate(self) -> tuple[bytes, bytes]:
        return self.stdout_bytes, self.stderr_bytes


def _runner(stdout=b"", stderr=b"", returncode=0, raise_not_found=False):
    captured: dict = {}

    async def run_subprocess(*args, **kwargs):
        if raise_not_found:
            raise FileNotFoundError("claude not found")
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeProcess(stdout, stderr, returncode)

    run_subprocess.captured = captured
    return run_subprocess


async def test_send_message_returns_stdout():
    runner = _runner(stdout=b"hello from claude\n")
    provider = ClaudeCodeProvider(run_subprocess=runner)
    response = await provider.send_message("hi")
    assert response.content == "hello from claude"
    assert response.provider == "claude_code"
    assert response.stub is False


async def test_send_message_passes_prompt_flag():
    runner = _runner(stdout=b"ok")
    provider = ClaudeCodeProvider(command="claude", run_subprocess=runner)
    await provider.send_message("hi")
    assert runner.captured["args"] == ("claude", "-p", "hi")


async def test_send_message_includes_history_in_prompt():
    runner = _runner(stdout=b"ok")
    provider = ClaudeCodeProvider(run_subprocess=runner)
    context = [ProviderMessage(role="user", content="earlier")]
    await provider.send_message("hi", context=context)
    prompt = runner.captured["args"][2]
    assert "earlier" in prompt
    assert prompt.endswith("user: hi")


async def test_send_message_reports_nonzero_exit():
    runner = _runner(stderr=b"boom", returncode=1)
    provider = ClaudeCodeProvider(run_subprocess=runner)
    response = await provider.send_message("hi")
    assert "claude error: boom" in response.content


async def test_send_message_reports_missing_cli():
    runner = _runner(raise_not_found=True)
    provider = ClaudeCodeProvider(command="claude", run_subprocess=runner)
    response = await provider.send_message("hi")
    assert "not found on PATH" in response.content


async def test_stream_response_yields_full_response():
    runner = _runner(stdout=b"streamed")
    provider = ClaudeCodeProvider(run_subprocess=runner)
    chunks = [chunk async for chunk in provider.stream_response("hi")]
    assert chunks == ["streamed"]
