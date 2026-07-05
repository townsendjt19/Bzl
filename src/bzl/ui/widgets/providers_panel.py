from textual.widgets import Static


class ProvidersPanel(Static):
    """Dumb presentational widget — receives plain strings, no service access."""

    def show_providers(self, names: list[str], preferred: str | None) -> None:
        if not names:
            self.update("[b]Providers[/b]\n(none registered)")
            return
        lines = [f"{'*' if name == preferred else ' '} {name} (stub)" for name in names]
        self.update("[b]Providers[/b]\n" + "\n".join(lines))
