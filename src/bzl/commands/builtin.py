from bzl.commands.registry import CommandContext, CommandRegistry, CommandResult


def register_all(registry: CommandRegistry) -> None:
    @registry.command("help", "List all available commands")
    async def help_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        lines = [f"{c.name} — {c.description}" for c in registry.all()]
        return CommandResult(message="\n".join(lines))

    @registry.command("status", "Show active project, git state, and providers")
    async def status_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(message="no active project")

        branch = ctx.git_service.get_branch()
        status = ctx.git_service.get_status()
        providers = ", ".join(ctx.provider_registry.list_providers()) or "none"

        if not status.is_git_repo:
            git_line = "not a git repo"
        else:
            git_line = f"branch={branch.branch or '(detached)'} clean={status.is_clean}"

        return CommandResult(
            message=(f"project: {project.name}\n" f"git: {git_line}\n" f"providers: {providers}")
        )

    @registry.command("projects", "List configured projects")
    async def projects_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        projects = ctx.project_service.list_projects()
        if not projects:
            return CommandResult(message="no projects configured")
        active = ctx.active_project
        lines = [
            f"{'*' if active and p.name == active.name else ' '} {p.name} — {p.path}"
            for p in projects
        ]
        return CommandResult(message="\n".join(lines))

    @registry.command("config", "Show the active project's resolved config")
    async def config_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(message="no active project")
        path, exists = ctx.project_service.resolve_path(project)
        return CommandResult(
            message=(
                f"name: {project.name}\n"
                f"description: {project.description}\n"
                f"path: {path} (exists={exists})\n"
                f"tags: {', '.join(project.tags) or '(none)'}\n"
                f"preferred_provider: {project.preferred_provider or '(none)'}"
            )
        )

    @registry.command("clear", "Clear the activity log")
    async def clear_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        ctx.activity_log.clear()
        return CommandResult(message="activity log cleared")

    @registry.command("exit", "Exit Bzl", aliases=("quit",))
    async def exit_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult(message="exiting", should_exit=True)
