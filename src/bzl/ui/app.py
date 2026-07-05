from textual.app import App

from bzl.commands.registry import CommandContext, CommandRegistry
from bzl.ui.dashboard import DashboardScreen


class BzlApp(App[None]):
    CSS_PATH = "styles/dashboard.tcss"

    def __init__(self, ctx: CommandContext, command_registry: CommandRegistry) -> None:
        super().__init__()
        self.ctx = ctx
        self.command_registry = command_registry

    def on_mount(self) -> None:
        persisted_theme = self.ctx.state_service.state.theme
        try:
            self.theme = persisted_theme
        except Exception:  # noqa: BLE001 - invalid persisted theme must not crash startup
            self.ctx.logger.warning("unknown persisted theme: %r", persisted_theme)
        self.push_screen(DashboardScreen(self.ctx, self.command_registry))
