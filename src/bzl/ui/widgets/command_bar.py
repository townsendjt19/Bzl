from textual.binding import Binding
from textual.message import Message
from textual.widgets import Input


class CommandBar(Input):
    """Dumb presentational widget — emits a message on submit, never calls services.

    Knows a static list of command names (passed in at construction) purely
    to offer tab-completion; it does not look them up itself.
    """

    BINDINGS = [
        Binding("up", "history_prev", "Previous command", show=False),
        Binding("down", "history_next", "Next command", show=False),
        Binding("tab", "complete", "Complete command", show=False),
        Binding("f2", "open_composer", "Multi-line editor", show=True),
    ]

    class CommandSubmitted(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class ComposeRequested(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def __init__(self, command_names: list[str] | None = None, id: str | None = None) -> None:
        super().__init__(placeholder="Type a command (help, status, projects, exit...)", id=id)
        self._command_names = sorted(command_names or [])
        self._history: list[str] = []
        self._history_index: int = 0

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value
        self.value = ""
        if text.strip():
            self._history.append(text)
        self._history_index = len(self._history)
        self.post_message(self.CommandSubmitted(text))

    def action_history_prev(self) -> None:
        if not self._history or self._history_index == 0:
            return
        self._history_index -= 1
        self.value = self._history[self._history_index]
        self.cursor_position = len(self.value)

    def action_history_next(self) -> None:
        if self._history_index >= len(self._history):
            return
        self._history_index += 1
        if self._history_index == len(self._history):
            self.value = ""
        else:
            self.value = self._history[self._history_index]
        self.cursor_position = len(self.value)

    def action_complete(self) -> None:
        prefix = self.value
        if not prefix:
            return
        matches = [name for name in self._command_names if name.startswith(prefix)]
        if matches:
            self.value = matches[0]
            self.cursor_position = len(self.value)

    def action_open_composer(self) -> None:
        self.post_message(self.ComposeRequested(self.value))

    def set_value_and_focus(self, text: str) -> None:
        # Input is single-line; embedded newlines corrupt its rendering, so
        # flatten multi-line compose text into one line before it lands here.
        self.value = " ".join(text.splitlines())
        self.cursor_position = len(self.value)
        self.focus()
