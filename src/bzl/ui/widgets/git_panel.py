from textual.widgets import Static


class GitPanel(Static):
    """Dumb presentational widget — receives plain strings, no service access."""

    def show_not_a_repo(self) -> None:
        self.update("[b]Git[/b]\nnot a git repository")

    def show_status(
        self, branch: str, clean: bool, staged: int, modified: int, untracked: int
    ) -> None:
        state = "clean" if clean else f"staged={staged} modified={modified} untracked={untracked}"
        self.update(f"[b]Git[/b]\nbranch: {branch}\n{state}")
