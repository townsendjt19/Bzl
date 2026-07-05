from bzl.config.loader import load_memory, save_memory
from bzl.models.memory import MemoryFile
from bzl.services.memory_service import MemoryService


def test_get_notes_empty_by_default(tmp_path):
    service = MemoryService(MemoryFile(), tmp_path / "memory.local.yaml")
    assert service.get_notes("demo") == []


def test_add_note_appears_in_notes(tmp_path):
    service = MemoryService(MemoryFile(), tmp_path / "memory.local.yaml")
    service.add_note("demo", "uses pydantic v2")
    assert service.get_notes("demo") == ["uses pydantic v2"]


def test_notes_are_scoped_per_project(tmp_path):
    service = MemoryService(MemoryFile(), tmp_path / "memory.local.yaml")
    service.add_note("demo", "note for demo")
    assert service.get_notes("other") == []


def test_clear_removes_notes(tmp_path):
    service = MemoryService(MemoryFile(), tmp_path / "memory.local.yaml")
    service.add_note("demo", "note for demo")
    service.clear("demo")
    assert service.get_notes("demo") == []


def test_mutations_are_persisted_to_disk(tmp_path):
    path = tmp_path / "memory.local.yaml"
    service = MemoryService(MemoryFile(), path)
    service.add_note("demo", "note for demo")

    reloaded = load_memory(path)
    assert reloaded.notes["demo"] == ["note for demo"]


def test_load_memory_missing_file_returns_empty(tmp_path):
    memory = load_memory(tmp_path / "memory.local.yaml")
    assert memory == MemoryFile()


def test_save_memory_round_trips(tmp_path):
    path = tmp_path / "memory.local.yaml"
    memory = MemoryFile(notes={"demo": ["a", "b"]})
    save_memory(path, memory)
    assert load_memory(path) == memory
