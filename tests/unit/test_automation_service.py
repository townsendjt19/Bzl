import subprocess
from pathlib import Path

from bzl.services.automation_service import AutomationService


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def test_runs_each_command_and_reports_ok():
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return _completed(returncode=0, stdout="output\n")

    service = AutomationService(run_command=fake_run)
    results = service.run_startup_commands(["git pull", "echo hi"], cwd=Path("/tmp"))

    assert calls == ["git pull", "echo hi"]
    assert len(results) == 2
    assert "git pull (ok)" in results[0]
    assert "output" in results[0]


def test_reports_nonzero_exit_status():
    def fake_run(command, **kwargs):
        return _completed(returncode=1, stderr="failed")

    service = AutomationService(run_command=fake_run)
    results = service.run_startup_commands(["bad-command"], cwd=Path("/tmp"))

    assert "exit 1" in results[0]
    assert "failed" in results[0]


def test_reports_timeout():
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(cmd=command, timeout=30)

    service = AutomationService(run_command=fake_run)
    results = service.run_startup_commands(["sleep 100"], cwd=Path("/tmp"))

    assert "timed out" in results[0]


def test_empty_commands_returns_empty_list():
    service = AutomationService(run_command=lambda *a, **k: _completed())
    assert service.run_startup_commands([], cwd=Path("/tmp")) == []
