from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import TextArea


class ComposeModal(ModalScreen[str | None]):
    """Multi-line editor for composing long commands/messages, e.g. detailed bug reports."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "submit", "Submit", show=True),
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
    """

    def __init__(self, initial_text: str = "") -> None:
        super().__init__()
        self._initial_text = initial_text

    def compose(self) -> ComposeResult:
        yield TextArea(self._initial_text, id="compose-text-area")

    def on_mount(self) -> None:
        self.query_one(TextArea).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        self.dismiss(self.query_one(TextArea).text)
