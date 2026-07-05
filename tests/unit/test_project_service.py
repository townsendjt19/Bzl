import pytest

from bzl.models.project import ProjectConfig, ProjectsFile
from bzl.services.project_service import ProjectNotFoundError, ProjectService


@pytest.fixture
def projects_file(tmp_path):
    existing_dir = tmp_path / "alpha_dir"
    existing_dir.mkdir()
    return ProjectsFile(
        projects=[
            ProjectConfig(name="alpha", path=str(existing_dir)),
            ProjectConfig(name="beta", path=str(tmp_path / "missing_dir")),
        ]
    )


def test_list_projects_returns_all(projects_file):
    service = ProjectService(projects_file)
    names = [p.name for p in service.list_projects()]
    assert names == ["alpha", "beta"]


def test_get_project_found(projects_file):
    service = ProjectService(projects_file)
    assert service.get_project("alpha").name == "alpha"


def test_get_project_not_found_raises(projects_file):
    service = ProjectService(projects_file)
    with pytest.raises(ProjectNotFoundError):
        service.get_project("nonexistent")


def test_active_project_defaults_to_first(projects_file):
    service = ProjectService(projects_file)
    assert service.active_project is not None
    assert service.active_project.name == "alpha"


def test_select_project_changes_active(projects_file):
    service = ProjectService(projects_file)
    service.select_project("beta")
    assert service.active_project.name == "beta"


def test_select_project_not_found_raises(projects_file):
    service = ProjectService(projects_file)
    with pytest.raises(ProjectNotFoundError):
        service.select_project("nonexistent")


def test_active_project_none_when_empty():
    service = ProjectService(ProjectsFile(projects=[]))
    assert service.active_project is None


def test_resolve_path_existing_dir(projects_file):
    service = ProjectService(projects_file)
    path, exists = service.resolve_path(service.get_project("alpha"))
    assert exists is True


def test_resolve_path_missing_dir(projects_file):
    service = ProjectService(projects_file)
    path, exists = service.resolve_path(service.get_project("beta"))
    assert exists is False
