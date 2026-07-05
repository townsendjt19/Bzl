import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from bzl.services.git_service import GitCommandError, GitService


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=["git"], returncode=returncode, stdout=stdout, stderr=stderr
    )


@pytest.fixture
def git_service():
    return GitService(cwd=Path("/tmp/whatever"))


def test_is_git_repo_true(git_service):
    with patch("subprocess.run", return_value=_completed(returncode=0)):
        assert git_service.is_git_repo() is True


def test_is_git_repo_false_on_nonzero_exit(git_service):
    with patch("subprocess.run", return_value=_completed(returncode=128)):
        assert git_service.is_git_repo() is False


def test_is_git_repo_false_when_git_missing(git_service):
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert git_service.is_git_repo() is False


def test_get_branch_not_a_repo(git_service):
    with patch("subprocess.run", return_value=_completed(returncode=128)):
        info = git_service.get_branch()
    assert info.is_git_repo is False
    assert info.branch is None


def test_get_branch_returns_current_branch(git_service):
    responses = [_completed(returncode=0), _completed(returncode=0, stdout="main\n")]
    with patch("subprocess.run", side_effect=responses):
        info = git_service.get_branch()
    assert info.is_git_repo is True
    assert info.branch == "main"
    assert info.is_detached is False


def test_get_status_not_a_repo(git_service):
    with patch("subprocess.run", return_value=_completed(returncode=128)):
        status = git_service.get_status()
    assert status.is_git_repo is False
    assert status.is_clean is True


def test_get_status_parses_porcelain_output(git_service):
    porcelain = "M  staged_file.py\n M modified_file.py\n?? new_file.py\n"
    responses = [_completed(returncode=0), _completed(returncode=0, stdout=porcelain)]
    with patch("subprocess.run", side_effect=responses):
        status = git_service.get_status()
    assert status.is_git_repo is True
    assert "staged_file.py" in status.staged
    assert "modified_file.py" in status.modified
    assert "new_file.py" in status.untracked
    assert status.is_clean is False


def test_get_recent_log_empty_repo_no_commits(git_service):
    responses = [
        _completed(returncode=0),
        _completed(
            returncode=128, stderr="fatal: your current branch does not have any commits yet"
        ),
    ]
    with patch("subprocess.run", side_effect=responses):
        log = git_service.get_recent_log()
    assert log == []


def test_get_recent_log_returns_lines(git_service):
    responses = [_completed(returncode=0), _completed(returncode=0, stdout="abc123 first commit\n")]
    with patch("subprocess.run", side_effect=responses):
        log = git_service.get_recent_log()
    assert log == ["abc123 first commit"]


def test_get_status_unexpected_error_raises(git_service):
    responses = [_completed(returncode=0), _completed(returncode=1, stderr="unexpected failure")]
    with patch("subprocess.run", side_effect=responses):
        with pytest.raises(GitCommandError):
            git_service.get_status()


def test_get_diff_not_a_repo(git_service):
    with patch("subprocess.run", return_value=_completed(returncode=128)):
        assert git_service.get_diff() == ""


def test_get_diff_returns_diff_text(git_service):
    responses = [_completed(returncode=0), _completed(returncode=0, stdout="diff --git a b\n")]
    with patch("subprocess.run", side_effect=responses):
        assert git_service.get_diff() == "diff --git a b\n"


def test_get_diff_falls_back_to_staged_when_no_head(git_service):
    responses = [
        _completed(returncode=0),
        _completed(returncode=128, stderr="fatal: ambiguous argument 'HEAD'"),
        _completed(returncode=0),
        _completed(returncode=0, stdout="diff --git a b\n"),
    ]
    with patch("subprocess.run", side_effect=responses):
        assert git_service.get_diff() == "diff --git a b\n"


def test_get_staged_diff_returns_diff_text(git_service):
    responses = [_completed(returncode=0), _completed(returncode=0, stdout="staged diff\n")]
    with patch("subprocess.run", side_effect=responses):
        assert git_service.get_staged_diff() == "staged diff\n"


def test_stage_all_raises_on_failure(git_service):
    with patch("subprocess.run", return_value=_completed(returncode=1, stderr="boom")):
        with pytest.raises(GitCommandError):
            git_service.stage_all()


def test_commit_raises_on_failure(git_service):
    with patch("subprocess.run", return_value=_completed(returncode=1, stderr="boom")):
        with pytest.raises(GitCommandError):
            git_service.commit("a message")


def test_commit_succeeds(git_service):
    with patch("subprocess.run", return_value=_completed(returncode=0)):
        git_service.commit("a message")
