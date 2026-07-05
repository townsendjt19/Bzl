from textual.widgets import Static

TEAL = "#3ED6C4"
VIOLET = "#7B61FF"

# Compact 2-line "BZL" mark for the header bar.
HEADER_LOGO_LINE_1 = "▛▀▜ ▄▄▟ ▌  "
HEADER_LOGO_LINE_2 = "▙▄▟ ▙▄▄ ▙▄▄"

# Larger 5-line "BZL" wordmark for the startup splash.
SPLASH_LOGO_ROWS = [
    "████  █████ █    ",
    "█   █    █  █    ",
    "████    █   █    ",
    "█   █  █    █    ",
    "████  █████ █████",
]


class LogoHeader(Static):
    """Compact block-character 'BZL' mark shown alongside the header."""

    def __init__(self, id: str | None = None) -> None:
        text = f"[{TEAL}]{HEADER_LOGO_LINE_1}[/]\n[{VIOLET}]{HEADER_LOGO_LINE_2}[/]"
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
