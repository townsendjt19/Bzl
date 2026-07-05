from textual.widgets import Static

TEAL = "#3ED6C4"
VIOLET = "#7B61FF"

ACTIVE_GLYPH = "●"
STUB_GLYPH = "○"


class ProvidersPanel(Static):
    """Dumb presentational widget — receives plain strings, no service access."""

    def show_providers(self, providers: list[tuple[str, bool]], preferred: str | None) -> None:
        if not providers:
            self.update("[b]Providers[/b]\n(none registered)")
            return
        lines = []
        for name, is_stub in providers:
            glyph, color = (STUB_GLYPH, VIOLET) if is_stub else (ACTIVE_GLYPH, TEAL)
            label = f"[b]{name}[/b]" if name == preferred else name
            lines.append(f"[{color}]{glyph}[/] {label}")
        self.update("[b]Providers[/b]\n" + "\n".join(lines))
