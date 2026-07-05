from collections.abc import Iterator

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header

from bzl.commands.registry import CommandContext, CommandRegistry
from bzl.ui.widgets.activity_log import ActivityLog
from bzl.ui.widgets.command_bar import CommandBar
from bzl.ui.widgets.git_panel import GitPanel
from bzl.ui.widgets.project_panel import ProjectPanel
from bzl.ui.widgets.providers_panel import ProvidersPanel


class DashboardScreen(Screen[None]):
    """Owns layout and all service access. Widgets underneath are dumb."""

    def __init__(self, ctx: CommandContext, command_registry: CommandRegistry) -> None:
        super().__init__()
        self.ctx = ctx
        self.command_registry = command_registry

    def compose(self) -> Iterator[Widget]:
        yield Header()
        with Vertical(id="dashboard-body"):
            with Horizontal(id="top-row"):
                yield ProjectPanel(id="project-panel")
                yield GitPanel(id="git-panel")
            yield ProvidersPanel(id="providers-panel")
            yield ActivityLog(id="activity-log")
            yield CommandBar(
                command_names=[c.name for c in self.command_registry.all()], id="command-bar"
            )
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_all()

    def refresh_all(self) -> None:
        self._refresh_project_panel()
        self._refresh_git_panel()
        self._refresh_providers_panel()
        self._refresh_activity_log()

    def _refresh_project_panel(self) -> None:
        panel = self.query_one("#project-panel", ProjectPanel)
        project = self.ctx.active_project
        if project is None:
            panel.show_no_project()
            return
        path, _exists = self.ctx.project_service.resolve_path(project)
        panel.show_project(project.name, str(path), project.description, project.tags)

    def _refresh_git_panel(self) -> None:
        panel = self.query_one("#git-panel", GitPanel)
        status = self.ctx.git_service.get_status()
        if not status.is_git_repo:
            panel.show_not_a_repo()
            return
        branch = self.ctx.git_service.get_branch()
        panel.show_status(
            branch=branch.branch or "(detached)",
            clean=status.is_clean,
            staged=len(status.staged),
            modified=len(status.modified),
            untracked=len(status.untracked),
        )

    def _refresh_providers_panel(self) -> None:
        panel = self.query_one("#providers-panel", ProvidersPanel)
        project = self.ctx.active_project
        preferred = project.preferred_provider if project else None
        panel.show_providers(self.ctx.provider_registry.list_providers(), preferred)

    def _refresh_activity_log(self) -> None:
        log = self.query_one("#activity-log", ActivityLog)
        lines = [f"[{e.timestamp}] {e.source}: {e.message}" for e in self.ctx.activity_log.all()]
        log.show_entries(lines)

    async def on_command_bar_command_submitted(self, event: CommandBar.CommandSubmitted) -> None:
        text = event.text.strip()
        if not text:
            return

        self.ctx.activity_log.add("command", f"> {text}")
        try:
            result = await self.command_registry.execute(text, self.ctx)
        except Exception as exc:  # noqa: BLE001 - UI must never crash on a bad command
            self.ctx.logger.exception("command execution failed: %s", text)
            self.ctx.activity_log.add("error", str(exc), level="error")
            self.refresh_all()
            return

        if result.message:
            self.ctx.activity_log.add("bzl", result.message)

        if result.theme:
            try:
                self.app.theme = result.theme
            except Exception:  # noqa: BLE001 - invalid theme name must not crash the UI
                self.ctx.activity_log.add(
                    "error", f"unknown theme: {result.theme!r}", level="error"
                )

        self.refresh_all()

        if result.should_exit:
            self.app.exit()
