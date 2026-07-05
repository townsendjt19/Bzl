import logging
from typing import TYPE_CHECKING

from bzl.commands import builtin, stubs
from bzl.commands.registry import CommandContext, CommandRegistry
from bzl.config.loader import (
    load_conversations,
    load_merged_projects,
    load_providers_config,
    load_state,
)
from bzl.config.paths import (
    resolve_configs_dir,
    resolve_conversations_file,
    resolve_providers_config_file,
    resolve_state_file,
)
from bzl.core.logging import configure_logging
from bzl.providers.chatgpt_provider import ChatGPTProvider
from bzl.providers.claude_code_provider import ClaudeCodeProvider
from bzl.providers.ollama_provider import OllamaProvider
from bzl.services.activity_log_service import ActivityLogService
from bzl.services.conversation_service import ConversationService
from bzl.services.git_service import GitService
from bzl.services.project_service import ProjectNotFoundError, ProjectService
from bzl.services.provider_registry import ProviderRegistry
from bzl.services.state_service import StateService

if TYPE_CHECKING:
    from bzl.ui.app import BzlApp

logger = logging.getLogger("bzl")


def build_context() -> CommandContext:
    """Build the fully-wired, UI-independent backend: config, services, commands.

    This is the piece that must work headlessly before any UI is touched.
    """
    configure_logging()

    configs_dir = resolve_configs_dir()
    projects_file = load_merged_projects(configs_dir)
    project_service = ProjectService(projects_file)

    state = load_state(resolve_state_file())
    if state.active_project is not None:
        try:
            project_service.select_project(state.active_project)
        except ProjectNotFoundError:
            pass
    state_service = StateService(state, resolve_state_file())

    active = project_service.active_project
    git_cwd = project_service.resolve_path(active)[0] if active else configs_dir.parent
    git_service = GitService(cwd=git_cwd)

    providers_config = load_providers_config(resolve_providers_config_file())
    provider_registry = ProviderRegistry()
    for provider in (
        OllamaProvider(host=providers_config.ollama.host, model=providers_config.ollama.model),
        ChatGPTProvider(),
        ClaudeCodeProvider(command=providers_config.claude_code.command),
    ):
        provider_registry.register(provider)

    activity_log = ActivityLogService()
    conversations = load_conversations(resolve_conversations_file())
    conversation_service = ConversationService(conversations, resolve_conversations_file())

    return CommandContext(
        project_service=project_service,
        git_service=git_service,
        provider_registry=provider_registry,
        activity_log=activity_log,
        state_service=state_service,
        conversation_service=conversation_service,
        logger=logger,
    )


def build_command_registry() -> CommandRegistry:
    registry = CommandRegistry()
    builtin.register_all(registry)
    stubs.register_all(registry)
    return registry


def build_app() -> "BzlApp":
    from bzl.ui.app import BzlApp

    ctx = build_context()
    registry = build_command_registry()
    ctx.activity_log.add("bzl", "Bzl started")
    return BzlApp(ctx=ctx, command_registry=registry)


def main() -> None:
    app = build_app()
    app.run()


if __name__ == "__main__":
    main()
