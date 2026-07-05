from textual.message import Message
from textual.widgets import Input


class CommandBar(Input):
    """Dumb presentational widget — emits a message on submit, never calls services."""

    class CommandSubmitted(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def __init__(self, id: str | None = None) -> None:
        super().__init__(placeholder="Type a command (help, status, projects, exit...)", id=id)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value
        self.value = ""
        self.post_message(self.CommandSubmitted(text))
