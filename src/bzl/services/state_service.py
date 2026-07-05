from pathlib import Path

from bzl.config.loader import save_state
from bzl.models.state import AppState

MAX_RECENT_PROJECTS = 5


class StateService:
    def __init__(self, state: AppState, path: Path) -> None:
        self.state = state
        self._path = path

    def record_project_switch(self, name: str) -> None:
        recent = [n for n in self.state.recent_projects if n != name]
        recent.insert(0, name)
        self.state.recent_projects = recent[:MAX_RECENT_PROJECTS]
        self.state.active_project = name
        self._save()

    def set_theme(self, name: str) -> None:
        self.state.theme = name
        self._save()

    def _save(self) -> None:
        save_state(self._path, self.state)
