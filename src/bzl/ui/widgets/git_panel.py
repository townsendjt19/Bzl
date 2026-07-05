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
        lines = ["[b]Git[/b]", f"branch: {branch}"]
        if clean:
            lines.append(f"[{TEAL}]{CLEAN_GLYPH}[/] clean")
        else:
            for label, count in (
                ("staged", staged),
                ("modified", modified),
                ("untracked", untracked),
            ):
                glyph, color = (DIRTY_GLYPH, VIOLET) if count else (CLEAN_GLYPH, TEAL)
                lines.append(f"[{color}]{glyph}[/] {label}={count}")
        self.update("\n".join(lines))
