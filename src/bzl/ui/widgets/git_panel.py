from textual.widgets import Static

TEAL = "#3ED6C4"
VIOLET = "#7B61FF"

CLEAN_GLYPH = "●"
DIRTY_GLYPH = "◆"


class GitPanel(Static):
    """Dumb presentational widget — receives plain strings, no service access."""

    def show_not_a_repo(self) -> None:
        self.update("[b]Git[/b]\nnot a git repository")

    def show_status(
        self, branch: str, clean: bool, staged: int, modified: int, untracked: int
    ) -> None:
        if clean:
            glyph, color, state = CLEAN_GLYPH, TEAL, "clean"
        else:
            glyph, color = DIRTY_GLYPH, VIOLET
            state = f"staged={staged} modified={modified} untracked={untracked}"
        self.update(f"[b]Git[/b]\nbranch: {branch}\n[{color}]{glyph}[/] {state}")
