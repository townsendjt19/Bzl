from textual.widgets import RichLog


class ActivityLog(RichLog):
    """Dumb presentational widget — receives plain strings, no service access."""

    def show_entries(self, lines: list[str]) -> None:
        self.clear()
        for line in lines:
            self.write(line)
