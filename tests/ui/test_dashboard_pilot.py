from bzl.commands.registry import CommandContext
from bzl.core.bootstrap import build_command_registry
from bzl.models.conversation import ConversationsFile
from bzl.models.memory import MemoryFile
from bzl.models.project import ProjectConfig, ProjectsFile
from bzl.models.state import AppState
from bzl.providers.ollama_provider import OllamaProvider
from bzl.services.activity_log_service import ActivityLogService
from bzl.services.automation_service import AutomationService
from bzl.services.conversation_service import ConversationService
from bzl.services.git_service import GitService
from bzl.services.memory_service import MemoryService
from bzl.services.project_service import ProjectService
from bzl.services.provider_registry import ProviderRegistry
from bzl.services.state_service import StateService
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
        state_service=StateService(AppState(), tmp_path / "state.local.yaml"),
        conversation_service=ConversationService(
            ConversationsFile(), tmp_path / "conversations.local.yaml"
        ),
        memory_service=MemoryService(MemoryFile(), tmp_path / "memory.local.yaml"),
        automation_service=AutomationService(),
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


def test_format_timestamp_converts_utc_to_local_without_offset_suffix():
    import re

    from bzl.ui.dashboard import DashboardScreen

    formatted = DashboardScreen._format_timestamp("2026-07-05T12:00:00+00:00")
    assert "+00:00" not in formatted
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", formatted)


async def test_f2_compose_confirm_populates_command_bar_without_executing(tmp_path):
    app = _build_test_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.screen.query_one("#command-bar")
        bar.focus()
        await pilot.press("f2")
        await pilot.pause()
        assert len(app.screen_stack) == 3

        text_area = app.screen.query_one("#compose-text-area")
        text_area.text = "status"
        await pilot.press("ctrl+s")
        await pilot.pause()

        assert len(app.screen_stack) == 2
        assert bar.value == "status"
        assert bar.cursor_position == len(bar.value)
        assert bar.has_focus


async def test_f2_compose_multiline_text_is_flattened_in_command_bar(tmp_path):
    app = _build_test_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.screen.query_one("#command-bar")
        bar.focus()
        await pilot.press("f2")
        await pilot.pause()

        text_area = app.screen.query_one("#compose-text-area")
        text_area.text = "line one\nline two\nline three"
        await pilot.press("ctrl+s")
        await pilot.pause()

        assert "\n" not in bar.value
        assert bar.value == "line one line two line three"
