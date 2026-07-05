from textual.timer import Timer
from textual.widgets import Static

TEAL = "#3ED6C4"
VIOLET = "#7B61FF"

SPINNER_FRAMES = ["▖", "▘", "▝", "▗"]


class ThinkingIndicator(Static):
    """Animated block-character spinner shown while awaiting a provider response."""

    def __init__(self, id: str | None = None) -> None:
        super().__init__("", id=id)
        self._frame = 0
        self._timer: Timer | None = None
        self.display = False

    def start(self) -> None:
        self._frame = 0
        self.display = True
        self._render_frame()
        self._timer = self.set_interval(0.12, self._tick)

    def stop(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self.display = False
        self.update("")

    def _tick(self) -> None:
        self._frame = (self._frame + 1) % len(SPINNER_FRAMES)
        self._render_frame()

    def _render_frame(self) -> None:
        glyph = SPINNER_FRAMES[self._frame]
        self.update(f"[{TEAL}]{glyph}[/] [{VIOLET}]thinking...[/]")
