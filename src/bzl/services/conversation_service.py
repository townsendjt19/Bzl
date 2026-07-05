from datetime import UTC, datetime
from pathlib import Path

from bzl.config.loader import save_conversations
from bzl.models.conversation import MAX_TURNS_PER_CONVERSATION, ConversationsFile, ConversationTurn
from bzl.models.provider import ProviderMessage


class ConversationService:
    def __init__(self, conversations: ConversationsFile, path: Path) -> None:
        self._conversations = conversations
        self._path = path

    @staticmethod
    def _key(project: str, provider: str) -> str:
        return f"{project}::{provider}"

    def get_history(self, project: str, provider: str) -> list[ProviderMessage]:
        turns = self._conversations.conversations.get(self._key(project, provider), [])
        return [ProviderMessage(role=t.role, content=t.content) for t in turns]

    def append_turn(self, project: str, provider: str, role: str, content: str) -> None:
        key = self._key(project, provider)
        turns = self._conversations.conversations.setdefault(key, [])
        timestamp = datetime.now(UTC).isoformat(timespec="seconds")
        turns.append(ConversationTurn(role=role, content=content, timestamp=timestamp))
        del turns[:-MAX_TURNS_PER_CONVERSATION]
        self._save()

    def clear(self, project: str, provider: str) -> None:
        self._conversations.conversations.pop(self._key(project, provider), None)
        self._save()

    def _save(self) -> None:
        save_conversations(self._path, self._conversations)
