from bzl.commands.registry import CommandContext
from bzl.core.bootstrap import build_command_registry
from bzl.models.project import ProjectConfig, ProjectsFile
from bzl.providers.ollama_provider import OllamaProvider
from bzl.services.activity_log_service import ActivityLogService
from bzl.services.git_service import GitService
from bzl.services.project_service import ProjectService
from bzl.services.provider_registry import ProviderRegistry
from bzl.ui.app import BzlApp
from bzl.ui.widgets.activity_log import ActivityLog
from bzl.ui.widgets.git_panel import GitPanel
from bzl.ui.widgets.project_panel import ProjectPanel


def _build_test_app(tmp_path) -> BzlApp:
    projects = ProjectsFile(projects=[ProjectConfig(name="demo", path=str(tmp_path))])
    provider_registry = ProviderRegistry()
    provider_registry.register(OllamaProvider())
    ctx = CommandContext(
        project_service=ProjectService(projects),
        git_service=GitService(cwd=tmp_path),
        provider_registry=provider_registry,
        activity_log=ActivityLogService(),
        logger=__import__("logging").getLogger("test"),
    )
    return BzlApp(ctx=ctx, command_registry=build_command_registry())


async def test_app_boots_and_dashboard_renders(tmp_path):
    app = _build_test_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.screen.query_one("#project-panel", ProjectPanel) is not None
        assert app.screen.query_one("#git-panel", GitPanel) is not None


async def test_command_bar_executes_command_without_crash(tmp_path):
    app = _build_test_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.screen.query_one("#command-bar")
        bar.value = "status"
        await pilot.press("enter")
        await pilot.pause()
        log = app.screen.query_one("#activity-log", ActivityLog)
        assert log is not None


async def test_unknown_command_does_not_crash_app(tmp_path):
    app = _build_test_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.screen.query_one("#command-bar")
        bar.value = "totally_bogus_command"
        await pilot.press("enter")
        await pilot.pause()
        assert app.is_running
