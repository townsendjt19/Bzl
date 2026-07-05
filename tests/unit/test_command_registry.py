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
from bzl.providers.ollama_provider import OllamaProvider
from bzl.services.activity_log_service import ActivityLogService
from bzl.services.git_service import GitService
from bzl.services.project_service import ProjectService
from bzl.services.provider_registry import ProviderRegistry


@pytest.fixture
def ctx(tmp_path):
    projects = ProjectsFile(projects=[ProjectConfig(name="demo", path=str(tmp_path))])
    provider_registry = ProviderRegistry()
    provider_registry.register(OllamaProvider())
    return CommandContext(
        project_service=ProjectService(projects),
        git_service=GitService(cwd=tmp_path),
        provider_registry=provider_registry,
        activity_log=ActivityLogService(),
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


def test_duplicate_registration_raises():
    reg = CommandRegistry()

    async def handler(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult(message="")

    from bzl.commands.registry import Command

    reg.register(Command(name="foo", description="", handler=handler))
    with pytest.raises(DuplicateCommandError):
        reg.register(Command(name="foo", description="", handler=handler))
