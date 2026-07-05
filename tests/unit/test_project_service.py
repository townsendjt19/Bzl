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


def test_validate_existing_dir_is_valid(projects_file):
    service = ProjectService(projects_file)
    status = service.validate(service.get_project("alpha"))
    assert status.status == "valid"
    assert status.reason is None


def test_validate_missing_dir_is_invalid(projects_file):
    service = ProjectService(projects_file)
    status = service.validate(service.get_project("beta"))
    assert status.status == "invalid"
    assert "does not exist" in status.reason


def test_validate_path_that_is_a_file_is_invalid(tmp_path):
    a_file = tmp_path / "not_a_dir.txt"
    a_file.write_text("hi", encoding="utf-8")
    projects = ProjectsFile(projects=[ProjectConfig(name="gamma", path=str(a_file))])
    service = ProjectService(projects)
    status = service.validate(service.get_project("gamma"))
    assert status.status == "invalid"
    assert "not a directory" in status.reason


def test_validate_detects_git_repo(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    projects = ProjectsFile(projects=[ProjectConfig(name="delta", path=str(repo_dir))])
    service = ProjectService(projects)
    status = service.validate(service.get_project("delta"))
    assert status.status == "valid"
    assert status.is_git is True


def test_validate_no_git_repo(projects_file):
    service = ProjectService(projects_file)
    status = service.validate(service.get_project("alpha"))
    assert status.is_git is False


def test_list_with_status_returns_all(projects_file):
    service = ProjectService(projects_file)
    statuses = service.list_with_status()
    assert {s.name: s.status for s in statuses} == {"alpha": "valid", "beta": "invalid"}
