from bzl.commands.registry import CommandContext, CommandRegistry, CommandResult
from bzl.models.provider import ProviderMessage
from bzl.services.project_service import ProjectNotFoundError


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
        return CommandResult(summary="\n".join(lines))

    @registry.command("status", "Show active project, git state, and providers")
    async def status_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(summary="no active project")

        branch = ctx.git_service.get_branch()
        status = ctx.git_service.get_status()
        providers = ", ".join(ctx.provider_registry.list_providers()) or "none"

        if not status.is_git_repo:
            git_line = "not a git repo"
        else:
            git_line = f"branch={branch.branch or '(detached)'} clean={status.is_clean}"

        return CommandResult(
            summary=(f"project: {project.name}\n" f"git: {git_line}\n" f"providers: {providers}")
        )

    @registry.command("projects", "List configured projects and their status")
    async def projects_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        statuses = ctx.project_service.list_with_status()
        if not statuses:
            return CommandResult(summary="no projects configured")
        active = ctx.active_project
        projects_by_name = {p.name: p for p in ctx.project_service.list_projects()}

        blocks = []
        for s in statuses:
            project = projects_by_name[s.name]
            icon = "✔" if s.status == "valid" else "⚠"
            marker = " (active)" if active and s.name == active.name else ""
            lines = [f"{icon} {s.name}{marker}", f"   path: {s.path}"]
            if s.status == "invalid":
                lines.append(f"   status: invalid ({s.reason})")
            else:
                lines.append("   status: valid")
                lines.append(f"   git: {'yes' if s.is_git else 'no'}")
            lines.append(f"   provider: {project.preferred_provider or '(none)'}")
            lines.append(f"   startup_commands: {len(project.startup_commands)}")
            blocks.append("\n".join(lines))

        return CommandResult(summary="\n\n".join(blocks))

    @registry.command("config", "Show the active project's resolved config")
    async def config_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(summary="no active project")
        path, exists = ctx.project_service.resolve_path(project)
        return CommandResult(
            summary=(
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
            return CommandResult(summary="usage: chat <message>")
        message = " ".join(args)
        project = ctx.active_project
        if project is None:
            return CommandResult(summary="no active project")

        preferred = project.preferred_provider
        provider = ctx.provider_registry.default_provider(preferred)
        prior_history = ctx.conversation_service.get_history(project.name, provider.name)
        context = _memory_context(ctx, project.name) + prior_history

        path, exists = ctx.project_service.resolve_path(project)
        if not exists:
            return CommandResult(summary=f"project path does not exist: {path}")

        execution = [
            f"loaded {len(prior_history)} prior turn(s) for {project.name}::{provider.name}",
            f"sent message to provider '{provider.name}'",
        ]
        response = await provider.send_message(message, context=context, cwd=path)

        ctx.conversation_service.append_turn(project.name, provider.name, "user", message)
        ctx.conversation_service.append_turn(
            project.name, provider.name, "assistant", response.content
        )
        execution.append("recorded user and assistant turns to conversation history")

        return CommandResult(
            execution=execution,
            ai=response.content,
            summary=f"received response from {provider.name}",
        )

    @registry.command("history", "Show or clear the active project's conversation history")
    async def history_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(summary="no active project")
        provider = ctx.provider_registry.default_provider(project.preferred_provider)

        if args and args[0] == "clear":
            ctx.conversation_service.clear(project.name, provider.name)
            return CommandResult(summary="conversation history cleared")

        turns = ctx.conversation_service.get_history(project.name, provider.name)
        if not turns:
            return CommandResult(summary="no conversation history yet")
        return CommandResult(summary="\n".join(f"{t.role}: {t.content}" for t in turns))

    @registry.command("review", "Request an AI code review of the working tree diff")
    async def review_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(summary="no active project")
        if not ctx.git_service.is_git_repo():
            return CommandResult(summary="not a git repository")

        diff = ctx.git_service.get_diff()
        if not diff.strip():
            return CommandResult(summary="no changes to review")

        provider = ctx.provider_registry.default_provider(project.preferred_provider)
        path, exists = ctx.project_service.resolve_path(project)
        if not exists:
            return CommandResult(summary=f"project path does not exist: {path}")
        memory = _memory_context(ctx, project.name)
        memory_block = f"{memory[0].content}\n\n" if memory else ""
        prompt = (
            f"{memory_block}Review the following git diff. Point out bugs, risks, "
            f"and improvements:\n\n{diff}"
        )
        execution = [
            f"computed working-tree diff ({len(diff.splitlines())} line(s))",
            f"sent diff to provider '{provider.name}' for review",
        ]
        response = await provider.send_message(prompt, cwd=path)

        return CommandResult(
            execution=execution,
            ai=response.content,
            summary=f"review complete via {provider.name}",
        )

    @registry.command("commit", "Stage all changes and commit with an AI-generated message")
    async def commit_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(summary="no active project")
        if not ctx.git_service.is_git_repo():
            return CommandResult(summary="not a git repository")

        ctx.git_service.stage_all()
        diff = ctx.git_service.get_staged_diff()
        if not diff.strip():
            return CommandResult(summary="nothing to commit")

        provider = ctx.provider_registry.default_provider(project.preferred_provider)
        path, exists = ctx.project_service.resolve_path(project)
        if not exists:
            return CommandResult(summary=f"project path does not exist: {path}")
        prompt = (
            "Write a single-line git commit message, imperative mood, no quotes, "
            f"summarizing this diff:\n\n{diff}"
        )
        execution = [
            "staged all changes (git add -A)",
            f"computed staged diff ({len(diff.splitlines())} line(s))",
            f"sent staged diff to provider '{provider.name}' for commit message generation",
        ]
        response = await provider.send_message(prompt, cwd=path)

        lines = [line.strip("\"'` ") for line in response.content.splitlines() if line.strip()]
        message = lines[0] if lines else "update"
        ctx.git_service.commit(message)
        execution.append(f"committed staged changes with message: {message}")

        return CommandResult(
            execution=execution,
            ai=response.content,
            summary=f"committed: {message}",
        )

    @registry.command("memory", "Show, add, or clear the active project's AI memory notes")
    async def memory_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        project = ctx.active_project
        if project is None:
            return CommandResult(summary="no active project")

        if not args:
            notes = ctx.memory_service.get_notes(project.name)
            if not notes:
                return CommandResult(summary="no memory notes yet")
            return CommandResult(summary="\n".join(f"- {n}" for n in notes))

        if args[0] == "clear":
            ctx.memory_service.clear(project.name)
            return CommandResult(summary="memory cleared")

        if args[0] == "add":
            note = " ".join(args[1:])
            if not note:
                return CommandResult(summary="usage: memory add <note>")
            ctx.memory_service.add_note(project.name, note)
            return CommandResult(summary="memory note added")

        return CommandResult(summary="usage: memory [add <note>|clear]")

    @registry.command("switch", "Switch the active project", aliases=("use",))
    async def switch_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(summary="usage: switch <project-name>")
        name = args[0]
        try:
            project = ctx.project_service.get_project(name)
        except ProjectNotFoundError as exc:
            return CommandResult(summary=str(exc))

        status = ctx.project_service.validate(project)
        if status.status == "invalid":
            return CommandResult(summary=f"cannot switch to {name!r}: {status.reason}")

        ctx.project_service.select_project(name)
        ctx.git_service.set_cwd(status.path)
        ctx.state_service.record_project_switch(name)

        execution: list[str] | None = None
        if project.startup_commands:
            execution = ctx.automation_service.run_startup_commands(
                project.startup_commands, status.path
            )

        return CommandResult(execution=execution, summary=f"switched to {name}")

    @registry.command("recent", "List recently switched-to projects")
    async def recent_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        names = ctx.state_service.state.recent_projects
        if not names:
            return CommandResult(summary="no recent projects yet")
        return CommandResult(summary="\n".join(names))

    @registry.command("theme", "Show or set the color theme")
    async def theme_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(summary=f"current: {ctx.state_service.state.theme}")
        name = args[0]
        ctx.state_service.set_theme(name)
        return CommandResult(summary=f"theme set to {name}", theme=name)

    @registry.command("clear", "Clear the activity log")
    async def clear_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        ctx.activity_log.clear()
        return CommandResult(summary="activity log cleared")

    @registry.command("exit", "Exit Bzl", aliases=("quit",))
    async def exit_command(ctx: CommandContext, args: list[str]) -> CommandResult:
        return CommandResult(summary="exiting", should_exit=True)
