from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static, TextArea


class ComposeModal(ModalScreen[str | None]):
    """Multi-line editor for composing long commands/messages, e.g. detailed bug reports."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "submit", "Submit", show=True, priority=True),
    ]

    DEFAULT_CSS = """
    ComposeModal {
        align: center middle;
    }
    ComposeModal > TextArea {
        width: 80%;
        height: 60%;
        border: thick $primary;
    }
    ComposeModal > .compose-hint {
        width: 80%;
        content-align: center middle;
        color: $text-muted;
    }
    """

    def __init__(self, initial_text: str = "") -> None:
        super().__init__()
        self._initial_text = initial_text
        self._confirming_discard = False

    def compose(self) -> ComposeResult:
        yield TextArea(self._initial_text, id="compose-text-area")
        yield Static(self._hint_text(), id="compose-hint", classes="compose-hint")

    def on_mount(self) -> None:
        self.query_one(TextArea).focus()

    def _hint_text(self) -> str:
        if self._confirming_discard:
            return "Discard draft? Press Esc again to confirm, or keep typing to cancel."
        return "Ctrl+S to insert into command bar  ·  Esc to cancel"

    def _set_hint(self) -> None:
        self.query_one("#compose-hint", Static).update(self._hint_text())

    def _is_dirty(self) -> bool:
        return self.query_one(TextArea).text != self._initial_text

    def action_cancel(self) -> None:
        if not self._is_dirty():
            self.dismiss(None)
            return
        if self._confirming_discard:
            self.dismiss(None)
            return
        self._confirming_discard = True
        self._set_hint()

    def action_submit(self) -> None:
        self.dismiss(self.query_one(TextArea).text)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if self._confirming_discard:
            self._confirming_discard = False
            self._set_hint()
