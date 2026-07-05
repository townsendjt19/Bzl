from bzl.commands.registry import CommandContext, CommandRegistry, CommandResult
from bzl.models.provider import ProviderMessage


def _memory_context(ctx: CommandContext, project_name: str) -> list[ProviderMessage]:
    notes = ctx.memory_service.get_notes(project_name)
    if not notes:
        return []
    notes_block = "\n".join(f"- {note}" for note in notes)
    return [ProviderMessage(role="system", content=f"Project memory notes:\n{notes_block}")]


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

    @registry.command("chat", "Chat with the active project's preferred AI provider")
    async def chat_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(message="usage: chat <message>")
        message = " ".join(args)
        project = ctx.active_project
        if project is None:
            return CommandResult(message="no active project")

        preferred = project.preferred_provider
        provider = ctx.provider_registry.default_provider(preferred)
        history = _memory_context(ctx, project.name) + ctx.conversation_service.get_history(
            project.name, provider.name
        )
        response = await provider.send_message(message, context=history)

        ctx.conversation_service.append_turn(project.name, provider.name, "user", message)
        ctx.conversation_service.append_turn(
            project.name, provider.name, "assistant", response.content
        )
        return CommandResult(message=response.content)

    @registry.command("history", "Show or clear the active project's conversation history")
    async def history_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(message="no active project")
        provider = ctx.provider_registry.default_provider(project.preferred_provider)

        if args and args[0] == "clear":
            ctx.conversation_service.clear(project.name, provider.name)
            return CommandResult(message="conversation history cleared")

        turns = ctx.conversation_service.get_history(project.name, provider.name)
        if not turns:
            return CommandResult(message="no conversation history yet")
        return CommandResult(message="\n".join(f"{t.role}: {t.content}" for t in turns))

    @registry.command("review", "Request an AI code review of the working tree diff")
    async def review_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(message="no active project")
        if not ctx.git_service.is_git_repo():
            return CommandResult(message="not a git repository")

        diff = ctx.git_service.get_diff()
        if not diff.strip():
            return CommandResult(message="no changes to review")

        provider = ctx.provider_registry.default_provider(project.preferred_provider)
        memory = _memory_context(ctx, project.name)
        memory_block = f"{memory[0].content}\n\n" if memory else ""
        prompt = (
            f"{memory_block}Review the following git diff. Point out bugs, risks, "
            f"and improvements:\n\n{diff}"
        )
        response = await provider.send_message(prompt)
        return CommandResult(message=response.content)

    @registry.command("commit", "Stage all changes and commit with an AI-generated message")
    async def commit_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(message="no active project")
        if not ctx.git_service.is_git_repo():
            return CommandResult(message="not a git repository")

        ctx.git_service.stage_all()
        diff = ctx.git_service.get_staged_diff()
        if not diff.strip():
            return CommandResult(message="nothing to commit")

        provider = ctx.provider_registry.default_provider(project.preferred_provider)
        prompt = (
            "Write a single-line git commit message, imperative mood, no quotes, "
            f"summarizing this diff:\n\n{diff}"
        )
        response = await provider.send_message(prompt)
        lines = [line.strip("\"'` ") for line in response.content.splitlines() if line.strip()]
        message = lines[0] if lines else "update"
        ctx.git_service.commit(message)
        return CommandResult(message=f"committed: {message}")

    @registry.command("memory", "Show, add, or clear the active project's AI memory notes")
    async def memory_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(message="no active project")

        if not args:
            notes = ctx.memory_service.get_notes(project.name)
            if not notes:
                return CommandResult(message="no memory notes yet")
            return CommandResult(message="\n".join(f"- {n}" for n in notes))

        if args[0] == "clear":
            ctx.memory_service.clear(project.name)
            return CommandResult(message="memory cleared")

        if args[0] == "add":
            note = " ".join(args[1:])
            if not note:
                return CommandResult(message="usage: memory add <note>")
            ctx.memory_service.add_note(project.name, note)
            return CommandResult(message="memory note added")

        return CommandResult(message="usage: memory [add <note>|clear]")

    @registry.command("switch", "Switch the active project", aliases=("use",))
    async def switch_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(message="usage: switch <project-name>")
        name = args[0]
        ctx.project_service.select_project(name)
        project = ctx.project_service.get_project(name)
        path, _exists = ctx.project_service.resolve_path(project)
        ctx.git_service.set_cwd(path)
        ctx.state_service.record_project_switch(name)

        if project.startup_commands:
            results = ctx.automation_service.run_startup_commands(project.startup_commands, path)
            for line in results:
                ctx.activity_log.add("automation", line)

        return CommandResult(message=f"switched to {name}")

    @registry.command("recent", "List recently switched-to projects")
    async def recent_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        names = ctx.state_service.state.recent_projects
        if not names:
            return CommandResult(message="no recent projects yet")
        return CommandResult(message="\n".join(names))

    @registry.command("theme", "Show or set the color theme")
    async def theme_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(message=f"current: {ctx.state_service.state.theme}")
        name = args[0]
        ctx.state_service.set_theme(name)
        return CommandResult(message=f"theme set to {name}", theme=name)

    @registry.command("clear", "Clear the activity log")
    async def clear_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        ctx.activity_log.clear()
        return CommandResult(message="activity log cleared")

    @registry.command("exit", "Exit Bzl", aliases=("quit",))
    async def exit_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult(message="exiting", should_exit=True)
