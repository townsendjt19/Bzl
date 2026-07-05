import logging
import subprocess
from collections.abc import AsyncIterator

import pytest

from bzl.commands import builtin, stubs
from bzl.commands.registry import (
    CommandContext,
    CommandNotFoundError,
    CommandRegistry,
    CommandResult,
    DuplicateCommandError,
)
from bzl.models.conversation import ConversationsFile
from bzl.models.memory import MemoryFile
from bzl.models.project import ProjectConfig, ProjectsFile
from bzl.models.provider import ProviderMessage, ProviderResponse
from bzl.models.state import AppState
from bzl.services.activity_log_service import ActivityLogService
from bzl.services.automation_service import AutomationService
from bzl.services.conversation_service import ConversationService
from bzl.services.git_service import GitService
from bzl.services.memory_service import MemoryService
from bzl.services.project_service import ProjectService
from bzl.services.provider_registry import ProviderRegistry
from bzl.services.state_service import StateService


class FakeProvider:
    """Offline stand-in for a real AIProvider, echoing back what it received."""

    name = "ollama"

    async def send_message(
        self, message: str, *, context: list[ProviderMessage] | None = None
    ) -> ProviderResponse:
        history_len = len(context or [])
        return ProviderResponse(
            content=f"[fake:{self.name}] history={history_len} received: {message}",
            provider=self.name,
            stub=False,
        )

    async def stream_response(
        self, message: str, *, context: list[ProviderMessage] | None = None
    ) -> AsyncIterator[str]:
        yield f"[fake:{self.name}] {message}"


def _init_git_repo(path):
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True)
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True, check=True)


@pytest.fixture
def ctx(tmp_path):
    demo_dir = tmp_path / "demo"
    demo_dir.mkdir()
    _init_git_repo(demo_dir)
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    projects = ProjectsFile(
        projects=[
            ProjectConfig(name="demo", path=str(demo_dir)),
            ProjectConfig(name="other", path=str(other_dir)),
            ProjectConfig(
                name="auto", path=str(other_dir), startup_commands=["echo hello-startup"]
            ),
        ]
    )
    provider_registry = ProviderRegistry()
    provider_registry.register(FakeProvider())
    return CommandContext(
        project_service=ProjectService(projects),
        git_service=GitService(cwd=demo_dir),
        provider_registry=provider_registry,
        activity_log=ActivityLogService(),
        state_service=StateService(AppState(), tmp_path / "state.local.yaml"),
        conversation_service=ConversationService(
            ConversationsFile(), tmp_path / "conversations.local.yaml"
        ),
        memory_service=MemoryService(MemoryFile(), tmp_path / "memory.local.yaml"),
        automation_service=AutomationService(),
        logger=logging.getLogger("test"),
    )


@pytest.fixture
def registry():
    reg = CommandRegistry()
    builtin.register_all(reg)
    stubs.register_all(reg)
    return reg


async def test_help_lists_all_commands(registry, ctx):
    result = await registry.execute("help", ctx)
    assert "status" in result.summary
    assert "exit" in result.summary


async def test_status_reports_project_and_providers(registry, ctx):
    result = await registry.execute("status", ctx)
    assert "project: demo" in result.summary
    assert "ollama" in result.summary


async def test_projects_lists_configured_projects(registry, ctx):
    result = await registry.execute("projects", ctx)
    assert "demo" in result.summary


async def test_exit_signals_should_exit(registry, ctx):
    result = await registry.execute("exit", ctx)
    assert result.should_exit is True


async def test_unknown_command_raises(registry, ctx):
    with pytest.raises(CommandNotFoundError):
        await registry.execute("bogus", ctx)


async def test_clear_empties_activity_log(registry, ctx):
    ctx.activity_log.add("test", "something happened")
    assert ctx.activity_log.all()
    await registry.execute("clear", ctx)
    assert ctx.activity_log.all() == []


async def test_chat_returns_provider_response(registry, ctx):
    result = await registry.execute("chat hello there", ctx)
    assert "[fake:ollama]" in result.ai
    assert "history=0" in result.ai
    assert result.summary == "received response from ollama"
    assert any("sent message to provider" in line for line in result.execution)


async def test_chat_feeds_prior_turns_as_history(registry, ctx):
    await registry.execute("chat first message", ctx)
    result = await registry.execute("chat second message", ctx)
    assert "history=2" in result.ai


async def test_chat_without_message_shows_usage(registry, ctx):
    result = await registry.execute("chat", ctx)
    assert "usage" in result.summary
    assert result.ai is None
    assert result.execution is None


async def test_history_empty_by_default(registry, ctx):
    result = await registry.execute("history", ctx)
    assert "no conversation history" in result.summary


async def test_history_shows_prior_turns(registry, ctx):
    await registry.execute("chat hello", ctx)
    result = await registry.execute("history", ctx)
    assert "user: hello" in result.summary
    assert "assistant:" in result.summary


async def test_history_clear_empties_it(registry, ctx):
    await registry.execute("chat hello", ctx)
    await registry.execute("history clear", ctx)
    result = await registry.execute("history", ctx)
    assert "no conversation history" in result.summary


async def test_switch_changes_active_project_and_git_cwd(registry, ctx):
    result = await registry.execute("switch other", ctx)
    assert "switched to other" in result.summary
    assert ctx.active_project.name == "other"
    expected_path, _exists = ctx.project_service.resolve_path(ctx.active_project)
    assert ctx.git_service.cwd == expected_path


async def test_switch_records_recent_project(registry, ctx):
    await registry.execute("switch other", ctx)
    assert ctx.state_service.state.recent_projects == ["other"]


async def test_switch_unknown_project_raises(registry, ctx):
    from bzl.services.project_service import ProjectNotFoundError

    with pytest.raises(ProjectNotFoundError):
        await registry.execute("switch bogus", ctx)


async def test_recent_lists_switched_projects(registry, ctx):
    await registry.execute("switch other", ctx)
    result = await registry.execute("recent", ctx)
    assert "other" in result.summary


async def test_recent_empty_by_default(registry, ctx):
    result = await registry.execute("recent", ctx)
    assert "no recent projects" in result.summary


async def test_theme_shows_current_by_default(registry, ctx):
    result = await registry.execute("theme", ctx)
    assert "textual-dark" in result.summary


async def test_theme_sets_and_persists(registry, ctx):
    result = await registry.execute("theme nord", ctx)
    assert result.theme == "nord"
    assert ctx.state_service.state.theme == "nord"


async def test_review_reports_no_changes_on_clean_repo(registry, ctx):
    result = await registry.execute("review", ctx)
    assert result.summary == "no changes to review"
    assert result.ai is None
    assert result.execution is None


async def test_review_sends_diff_to_provider(registry, ctx):
    (ctx.git_service.cwd / "README.md").write_text("hello world\n", encoding="utf-8")
    result = await registry.execute("review", ctx)
    assert "[fake:ollama]" in result.ai
    assert "hello world" in result.ai
    assert result.summary == "review complete via ollama"
    assert any("sent diff to provider" in line for line in result.execution)


async def test_review_includes_memory_notes(registry, ctx):
    (ctx.git_service.cwd / "README.md").write_text("hello world\n", encoding="utf-8")
    ctx.memory_service.add_note("demo", "this project uses tabs, not spaces")
    result = await registry.execute("review", ctx)
    assert "this project uses tabs, not spaces" in result.ai


async def test_review_not_a_git_repo(registry, ctx):
    other_path, _exists = ctx.project_service.resolve_path(ctx.project_service.get_project("other"))
    ctx.git_service.set_cwd(other_path)
    result = await registry.execute("review", ctx)
    assert result.summary == "not a git repository"


async def test_commit_reports_nothing_to_commit_on_clean_repo(registry, ctx):
    result = await registry.execute("commit", ctx)
    assert result.summary == "nothing to commit"


async def test_commit_stages_and_commits_with_generated_message(registry, ctx):
    (ctx.git_service.cwd / "new_file.py").write_text("print('hi')\n", encoding="utf-8")
    log_before = ctx.git_service.get_recent_log()

    result = await registry.execute("commit", ctx)

    assert result.summary.startswith("committed: [fake:ollama]")
    assert "[fake:ollama]" in result.ai
    assert any("staged all changes" in line for line in result.execution)
    assert any("committed staged changes with message" in line for line in result.execution)
    log_after = ctx.git_service.get_recent_log()
    assert len(log_after) == len(log_before) + 1
    assert ctx.git_service.get_status().is_clean


async def test_memory_empty_by_default(registry, ctx):
    result = await registry.execute("memory", ctx)
    assert "no memory notes yet" in result.summary


async def test_memory_add_and_list(registry, ctx):
    await registry.execute("memory add uses pydantic v2", ctx)
    result = await registry.execute("memory", ctx)
    assert "uses pydantic v2" in result.summary


async def test_memory_add_without_note_shows_usage(registry, ctx):
    result = await registry.execute("memory add", ctx)
    assert "usage" in result.summary


async def test_memory_clear_empties_it(registry, ctx):
    await registry.execute("memory add uses pydantic v2", ctx)
    await registry.execute("memory clear", ctx)
    result = await registry.execute("memory", ctx)
    assert "no memory notes yet" in result.summary


async def test_memory_is_injected_into_chat_context(registry, ctx):
    await registry.execute("memory add remember this fact", ctx)
    result = await registry.execute("chat hello", ctx)
    assert "history=1" in result.ai


async def test_switch_runs_startup_commands(registry, ctx):
    result = await registry.execute("switch auto", ctx)
    assert result.execution is not None
    assert any("echo hello-startup" in line for line in result.execution)
    assert any("hello-startup" in line for line in result.execution)


async def test_switch_without_startup_commands_has_no_execution(registry, ctx):
    result = await registry.execute("switch other", ctx)
    assert result.execution is None


def test_duplicate_registration_raises():
    reg = CommandRegistry()

    async def handler(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult(summary="")

    from bzl.commands.registry import Command

    reg.register(Command(name="foo", description="", handler=handler))
    with pytest.raises(DuplicateCommandError):
        reg.register(Command(name="foo", description="", handler=handler))
