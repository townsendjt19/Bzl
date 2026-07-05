from pydantic import BaseModel, Field

MAX_TURNS_PER_CONVERSATION = 50


class ConversationTurn(BaseModel):
    role: str
    content: str
    timestamp: str


class ConversationsFile(BaseModel):
    """Maps "<project>::<provider>" -> its turns, persisted to a gitignored local file."""

    conversations: dict[str, list[ConversationTurn]] = Field(default_factory=dict)
