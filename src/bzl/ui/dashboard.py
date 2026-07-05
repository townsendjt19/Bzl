from collections.abc import Iterator
from datetime import datetime

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Header

from bzl.commands.registry import CommandContext, CommandRegistry
from bzl.ui.widgets.activity_log import ActivityLog
from bzl.ui.widgets.command_bar import CommandBar
from bzl.ui.widgets.compose_modal import ComposeModal
from bzl.ui.widgets.git_panel import GitPanel
from bzl.ui.widgets.logo import LogoHeader, SplashBanner
from bzl.ui.widgets.project_panel import ProjectPanel
from bzl.ui.widgets.providers_panel import ProvidersPanel
from bzl.ui.widgets.thinking_indicator import ThinkingIndicator


class DashboardScreen(Screen[None]):
    """Owns layout and all service access. Widgets underneath are dumb."""

    def __init__(self, ctx: CommandContext, command_registry: CommandRegistry) -> None:
        super().__init__()
        self.ctx = ctx
        self.command_registry = command_registry

    def compose(self) -> Iterator[Widget]:
        yield Header()
        with Vertical(id="dashboard-body"):
            yield SplashBanner(id="splash-banner")
            yield LogoHeader(id="logo-header")
            with Horizontal(id="top-row"):
                yield ProjectPanel(id="project-panel")
                yield GitPanel(id="git-panel")
            yield ProvidersPanel(id="providers-panel")
            yield ThinkingIndicator(id="thinking-indicator")
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
        names = self.ctx.provider_registry.list_providers()
        providers = [(name, self.ctx.provider_registry.get(name).is_stub) for name in names]
        panel.show_providers(providers, preferred)

    def _refresh_activity_log(self) -> None:
        log = self.query_one("#activity-log", ActivityLog)
        lines = [
            f"[{self._format_timestamp(e.timestamp)}] {e.source} [{e.section}]: {e.message}"
            for e in self.ctx.activity_log.all()
        ]
        log.show_entries(lines)

    @staticmethod
    def _format_timestamp(raw: str) -> str:
        try:
            return datetime.fromisoformat(raw).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return raw

    async def on_command_bar_command_submitted(self, event: CommandBar.CommandSubmitted) -> None:
        await self._execute_command_text(event.text)

    def on_command_bar_compose_requested(self, event: CommandBar.ComposeRequested) -> None:
        def handle_result(result: str | None) -> None:
            if result is not None:
                self.query_one("#command-bar", CommandBar).set_value_and_focus(result)
            # The modal covers the full screen while open; force a full repaint on
            # return so no stale cells from it linger over the dashboard/command bar.
            self.refresh(layout=True)

        self.app.push_screen(ComposeModal(event.text), handle_result)

    async def _execute_command_text(self, raw_text: str) -> None:
        text = raw_text.strip()
        if not text:
            return

        self.ctx.activity_log.add("command", f"> {text}", section="system")
        self._refresh_activity_log()
        indicator = self.query_one("#thinking-indicator", ThinkingIndicator)
        indicator.start()
        try:
            result = await self.command_registry.execute(text, self.ctx)
        except Exception as exc:  # noqa: BLE001 - UI must never crash on a bad command
            self.ctx.logger.exception("command execution failed: %s", text)
            self.ctx.activity_log.add("error", str(exc), level="error", section="system")
            self.refresh_all()
            return
        finally:
            indicator.stop()

        # Logged in this fixed order — execution (mechanical trace) before ai
        # (raw provider output) before summary — so AI output never interleaves
        # with execution traces or system log lines within a single command.
        for line in result.execution or []:
            self.ctx.activity_log.add("execution", line, section="execution")
        if result.ai:
            self.ctx.activity_log.add("ai", result.ai, section="ai")
        if result.summary:
            self.ctx.activity_log.add("bzl", result.summary, section="summary")

        if result.theme:
            try:
                self.app.theme = result.theme
            except Exception:  # noqa: BLE001 - invalid theme name must not crash the UI
                self.ctx.activity_log.add(
                    "error", f"unknown theme: {result.theme!r}", level="error"
                )

        if result.clipboard is not None:
            self.app.copy_to_clipboard(result.clipboard)

        self.refresh_all()

        if result.should_exit:
            self.app.exit()
