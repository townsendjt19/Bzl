import logging

import pytest

from bzl.commands import builtin, stubs
from bzl.commands.registry import (
    CommandContext,
    CommandNotFoundError,
    CommandRegistry,
    CommandResult,
    DuplicateCommandError,
)
from bzl.models.project import ProjectConfig, ProjectsFile
from bzl.models.state import AppState
from bzl.providers.ollama_provider import OllamaProvider
from bzl.services.activity_log_service import ActivityLogService
from bzl.services.git_service import GitService
from bzl.services.project_service import ProjectService
from bzl.services.provider_registry import ProviderRegistry
from bzl.services.state_service import StateService


@pytest.fixture
def ctx(tmp_path):
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    projects = ProjectsFile(
        projects=[
            ProjectConfig(name="demo", path=str(tmp_path)),
            ProjectConfig(name="other", path=str(other_dir)),
        ]
    )
    provider_registry = ProviderRegistry()
    provider_registry.register(OllamaProvider())
    return CommandContext(
        project_service=ProjectService(projects),
        git_service=GitService(cwd=tmp_path),
        provider_registry=provider_registry,
        activity_log=ActivityLogService(),
        state_service=StateService(AppState(), tmp_path / "state.local.yaml"),
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
    assert "status" in result.message
    assert "exit" in result.message


async def test_status_reports_project_and_providers(registry, ctx):
    result = await registry.execute("status", ctx)
    assert "project: demo" in result.message
    assert "ollama" in result.message


async def test_projects_lists_configured_projects(registry, ctx):
    result = await registry.execute("projects", ctx)
    assert "demo" in result.message


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


async def test_chat_stub_returns_provider_response(registry, ctx):
    result = await registry.execute("chat hello there", ctx)
    assert "stub:ollama" in result.message


async def test_switch_changes_active_project_and_git_cwd(registry, ctx):
    result = await registry.execute("switch other", ctx)
    assert "switched to other" in result.message
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
    assert "other" in result.message


async def test_recent_empty_by_default(registry, ctx):
    result = await registry.execute("recent", ctx)
    assert "no recent projects" in result.message


async def test_theme_shows_current_by_default(registry, ctx):
    result = await registry.execute("theme", ctx)
    assert "textual-dark" in result.message


async def test_theme_sets_and_persists(registry, ctx):
    result = await registry.execute("theme nord", ctx)
    assert result.theme == "nord"
    assert ctx.state_service.state.theme == "nord"


def test_duplicate_registration_raises():
    reg = CommandRegistry()

    async def handler(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult(message="")

    from bzl.commands.registry import Command

    reg.register(Command(name="foo", description="", handler=handler))
    with pytest.raises(DuplicateCommandError):
        reg.register(Command(name="foo", description="", handler=handler))
