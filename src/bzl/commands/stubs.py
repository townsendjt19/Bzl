from bzl.commands.registry import CommandContext, CommandRegistry, CommandResult


def register_all(registry: CommandRegistry) -> None:
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
