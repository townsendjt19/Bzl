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
        self.push_screen(DashboardScreen(self.ctx, self.command_registry))
