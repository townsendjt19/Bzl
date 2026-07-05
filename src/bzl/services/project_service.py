from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from bzl.models.project import ProjectConfig, ProjectsFile


class ProjectNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class ProjectStatus:
    name: str
    path: Path
    status: Literal["valid", "invalid"]
    reason: str | None = None
    is_git: bool = False


class ProjectService:
    def __init__(self, projects: ProjectsFile) -> None:
        self._projects = {p.name: p for p in projects.projects}
        self._active_name: str | None = next(iter(self._projects), None)

    def list_projects(self) -> list[ProjectConfig]:
        return list(self._projects.values())

    def get_project(self, name: str) -> ProjectConfig:
        try:
            return self._projects[name]
        except KeyError as exc:
            raise ProjectNotFoundError(f"no project named {name!r}") from exc

    def select_project(self, name: str) -> None:
        if name not in self._projects:
            raise ProjectNotFoundError(f"no project named {name!r}")
        self._active_name = name

    @property
    def active_project(self) -> ProjectConfig | None:
        if self._active_name is None:
            return None
        return self._projects[self._active_name]

    def resolve_path(self, project: ProjectConfig) -> tuple[Path, bool]:
        """Expand the project's configured path and report whether it exists."""
        path = Path(project.path).expanduser()
        return path, path.exists()

    def validate(self, project: ProjectConfig) -> ProjectStatus:
        """Check that a project's configured path is a usable directory."""
        path = Path(project.path).expanduser()
        if not path.exists():
            return ProjectStatus(
                project.name, path, "invalid", reason=f"path does not exist ({path})"
            )
        if not path.is_dir():
            return ProjectStatus(
                project.name, path, "invalid", reason=f"path is not a directory ({path})"
            )
        return ProjectStatus(project.name, path, "valid", is_git=(path / ".git").is_dir())

    def list_with_status(self) -> list[ProjectStatus]:
        return [self.validate(p) for p in self._projects.values()]
