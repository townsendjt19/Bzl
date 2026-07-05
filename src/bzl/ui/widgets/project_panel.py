from textual.widgets import Static


class ProjectPanel(Static):
    """Dumb presentational widget — receives plain strings, no service access."""

    def show_project(self, name: str, path: str, description: str, tags: list[str]) -> None:
        tag_str = ", ".join(tags) if tags else "(none)"
        self.update(f"[b]Project[/b]\n{name}\n{path}\n{description}\ntags: {tag_str}")

    def show_no_project(self) -> None:
        self.update("[b]Project[/b]\n(no project selected)")
