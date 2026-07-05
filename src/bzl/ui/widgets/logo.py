from textual.widgets import Static

TEAL = "#3ED6C4"
VIOLET = "#7B61FF"

# Larger 5-line "BZL" wordmark for the startup splash.
SPLASH_LOGO_ROWS = [
    "████  █████ █    ",
    "█   █    █  █    ",
    "████    █   █    ",
    "█   █  █    █    ",
    "████  █████ █████",
]


class LogoHeader(Static):
    """Compact 'BZL' mark shown alongside the header.

    Pixel-art letterforms need at least 5 rows to read as letters (see
    SPLASH_LOGO_ROWS) — at 2 rows the quadrant-block glyphs collapse into an
    illegible blob, so the compact mark uses plain bold text instead.
    """

    def __init__(self, id: str | None = None) -> None:
        text = f"[bold {TEAL}]B[/][bold {VIOLET}]Z[/][bold {TEAL}]L[/]"
        super().__init__(text, id=id)


class SplashBanner(Static):
    """Blocky 'BZL' wordmark shown briefly on launch, then hidden."""

    def __init__(self, id: str | None = None) -> None:
        text = "\n".join(f"[{TEAL if i < 3 else VIOLET}]{row}[/]" for i, row in enumerate(SPLASH_LOGO_ROWS))
        super().__init__(text, id=id)

    def on_mount(self) -> None:
        self.set_timer(1.2, self._dismiss)

    def _dismiss(self) -> None:
        self.display = False
