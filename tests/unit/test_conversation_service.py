from bzl.config.loader import load_conversations, save_conversations
from bzl.models.conversation import MAX_TURNS_PER_CONVERSATION, ConversationsFile
from bzl.services.conversation_service import ConversationService


def test_get_history_empty_by_default(tmp_path):
    service = ConversationService(ConversationsFile(), tmp_path / "conversations.local.yaml")
    assert service.get_history("demo", "ollama") == []


def test_append_turn_appears_in_history(tmp_path):
    service = ConversationService(ConversationsFile(), tmp_path / "conversations.local.yaml")
    service.append_turn("demo", "ollama", "user", "hello")
    history = service.get_history("demo", "ollama")
    assert len(history) == 1
    assert history[0].role == "user"
    assert history[0].content == "hello"


def test_history_is_scoped_per_project_and_provider(tmp_path):
    service = ConversationService(ConversationsFile(), tmp_path / "conversations.local.yaml")
    service.append_turn("demo", "ollama", "user", "hello")
    assert service.get_history("demo", "claude_code") == []
    assert service.get_history("other", "ollama") == []


def test_append_turn_caps_history_length(tmp_path):
    service = ConversationService(ConversationsFile(), tmp_path / "conversations.local.yaml")
    for i in range(MAX_TURNS_PER_CONVERSATION + 10):
        service.append_turn("demo", "ollama", "user", f"message {i}")
    history = service.get_history("demo", "ollama")
    assert len(history) == MAX_TURNS_PER_CONVERSATION
    assert history[-1].content == f"message {MAX_TURNS_PER_CONVERSATION + 9}"


def test_clear_removes_history(tmp_path):
    service = ConversationService(ConversationsFile(), tmp_path / "conversations.local.yaml")
    service.append_turn("demo", "ollama", "user", "hello")
    service.clear("demo", "ollama")
    assert service.get_history("demo", "ollama") == []


def test_mutations_are_persisted_to_disk(tmp_path):
    path = tmp_path / "conversations.local.yaml"
    service = ConversationService(ConversationsFile(), path)
    service.append_turn("demo", "ollama", "user", "hello")

    reloaded = load_conversations(path)
    turns = reloaded.conversations["demo::ollama"]
    assert len(turns) == 1
    assert turns[0].content == "hello"


def test_load_conversations_missing_file_returns_empty(tmp_path):
    conversations = load_conversations(tmp_path / "conversations.local.yaml")
    assert conversations == ConversationsFile()


def test_save_conversations_round_trips(tmp_path):
    path = tmp_path / "conversations.local.yaml"
    service = ConversationService(ConversationsFile(), path)
    service.append_turn("demo", "ollama", "user", "hello")
    service.append_turn("demo", "ollama", "assistant", "hi there")

    reloaded = load_conversations(path)
    save_conversations(path, reloaded)
    assert load_conversations(path) == reloaded
