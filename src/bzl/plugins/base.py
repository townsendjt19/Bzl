from typing import Protocol

from bzl.commands.registry import Command
from bzl.providers.base import AIProvider


class PluginCommand(Protocol):
    """Future extension point: a plugin contributes one or more Commands."""

    def commands(self) -> list[Command]: ...


class PluginProvider(Protocol):
    """Future extension point: a plugin contributes one or more AI providers."""

    def providers(self) -> list[AIProvider]: ...


class PluginWidget(Protocol):
    """Future extension point: a plugin contributes a UI widget/panel."""

    def widget_id(self) -> str: ...
