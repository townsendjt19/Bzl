import subprocess
from collections.abc import Callable
from pathlib import Path

CommandRunner = Callable[..., "subprocess.CompletedProcess[str]"]


class AutomationService:
    """Runs a project's configured startup_commands as plain shell commands."""

    def __init__(self, run_command: CommandRunner = subprocess.run) -> None:
        self._run_command = run_command

    def run_startup_commands(self, commands: list[str], cwd: Path) -> list[str]:
        results: list[str] = []
        for command in commands:
            try:
                result = self._run_command(
                    command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=30
                )
            except subprocess.TimeoutExpired:
                results.append(f"$ {command} (timed out)")
                continue
            status = "ok" if result.returncode == 0 else f"exit {result.returncode}"
            output = (result.stdout + result.stderr).strip()
            line = f"$ {command} ({status})"
            if output:
                line += f"\n{output}"
            results.append(line)
        return results
