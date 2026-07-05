from bzl.commands.registry import CommandContext, CommandRegistry, CommandResult


def register_all(registry: CommandRegistry) -> None:
    @registry.command("chat", "Chat with the active project's preferred AI provider (stub)")
    async def chat_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        message = " ".join(args) or "(no message)"
        project = ctx.active_project
        preferred = project.preferred_provider if project else None
        provider = ctx.provider_registry.default_provider(preferred)
        response = await provider.send_message(message)
        return CommandResult(message=response.content)

    @registry.command("review", "Request a code review from the active provider (stub)")
    async def review_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult(message="review is not yet implemented")

    @registry.command("deploy", "Run the active project's deploy workflow (stub)")
    async def deploy_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult(message="deploy is not yet implemented")

    @registry.command("git", "Show git status for the active project (real, via GitService)")
    async def git_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        status = ctx.git_service.get_status()
        if not status.is_git_repo:
            return CommandResult(message="not a git repository")
        lines = [
            f"staged: {len(status.staged)}",
            f"modified: {len(status.modified)}",
            f"untracked: {len(status.untracked)}",
        ]
        return CommandResult(message="\n".join(lines))
