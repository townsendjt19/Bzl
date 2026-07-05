from pathlib import Path

from bzl.config.loader import save_memory
from bzl.models.memory import MemoryFile


class MemoryService:
    def __init__(self, memory: MemoryFile, path: Path) -> None:
        self._memory = memory
        self._path = path

    def get_notes(self, project: str) -> list[str]:
        return list(self._memory.notes.get(project, []))

    def add_note(self, project: str, note: str) -> None:
        self._memory.notes.setdefault(project, []).append(note)
        self._save()

    def clear(self, project: str) -> None:
        self._memory.notes.pop(project, None)
        self._save()

    def _save(self) -> None:
        save_memory(self._path, self._memory)
