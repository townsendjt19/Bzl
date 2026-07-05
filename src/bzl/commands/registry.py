import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from bzl.models.project import ProjectConfig
from bzl.services.activity_log_service import ActivityLogService
from bzl.services.conversation_service import ConversationService
from bzl.services.git_service import GitService
from bzl.services.project_service import ProjectService
from bzl.services.provider_registry import ProviderRegistry
from bzl.services.state_service import StateService


@dataclass
class CommandContext:
    """The only way command handlers may reach the rest of the app.

    Handlers must not import services/providers directly — everything they
    need is exposed here.
    """

    project_service: ProjectService
    git_service: GitService
    provider_registry: ProviderRegistry
    activity_log: ActivityLogService
    state_service: StateService
    conversation_service: ConversationService
    logger: logging.Logger

    @property
    def active_project(self) -> ProjectConfig | None:
        return self.project_service.active_project


@dataclass
class CommandResult:
    message: str
    should_exit: bool = False
    theme: str | None = None


CommandHandler = Callable[[CommandContext, list[str]], Awaitable[CommandResult]]


@dataclass(frozen=True)
class Command:
    name: str
    description: str
    handler: CommandHandler
    aliases: tuple[str, ...] = ()


class DuplicateCommandError(Exception):
    pass


class CommandNotFoundError(Exception):
    pass


class CommandRegistry:
    """A plain, Textual-independent command registry.

    Deliberately does not touch textual.command — the public surface here
    (register/get/all/execute) is intentionally narrow so a future migration
    to Textual's command palette can wrap this registry without rewriting
    command handlers.
    """

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        for key in (command.name, *command.aliases):
            if key in self._commands:
                raise DuplicateCommandError(f"command name/alias already registered: {key!r}")
        for key in (command.name, *command.aliases):
            self._commands[key] = command

    def command(
        self, name: str, description: str, aliases: tuple[str, ...] = ()
    ) -> Callable[[CommandHandler], CommandHandler]:
        def decorator(handler: CommandHandler) -> CommandHandler:
            self.register(
                Command(name=name, description=description, handler=handler, aliases=aliases)
            )
            return handler

        return decorator

    def get(self, name: str) -> Command | None:
        return self._commands.get(name)

    def all(self) -> list[Command]:
        seen: set[str] = set()
        commands: list[Command] = []
        for command in self._commands.values():
            if command.name not in seen:
                seen.add(command.name)
                commands.append(command)
        return commands

    async def execute(self, raw_input: str, ctx: CommandContext) -> CommandResult:
        parts = raw_input.strip().split()
        if not parts:
            return CommandResult(message="")

        name, args = parts[0], parts[1:]
        command = self.get(name)
        if command is None:
            raise CommandNotFoundError(f"unknown command: {name!r}")

        return await command.handler(ctx, args)
