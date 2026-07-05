from pathlib import Path

from bzl.models.project import ProjectConfig, ProjectsFile


class ProjectNotFoundError(Exception):
    pass


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
