from textual.widgets import Static

TEAL = "#3ED6C4"
VIOLET = "#7B61FF"
INACTIVE = "dim"

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
            glyph = STUB_GLYPH if is_stub else ACTIVE_GLYPH
            if name == preferred:
                color = TEAL
            elif is_stub:
                color = VIOLET
            else:
                color = INACTIVE
            label = f"[b]{name}[/b]" if name == preferred else name
            lines.append(f"[{color}]{glyph}[/] {label}")
        self.update("[b]Providers[/b]\n" + "\n".join(lines))
