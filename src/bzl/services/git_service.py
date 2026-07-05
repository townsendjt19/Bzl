import logging
import subprocess
from pathlib import Path

from bzl.models.git import GitBranchInfo, GitStatus

logger = logging.getLogger(__name__)


class GitCommandError(Exception):
    """Raised when a git command fails unexpectedly (git present, is a repo, but errors)."""

    def __init__(self, cmd: list[str], returncode: int, stderr: str) -> None:
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"git command failed ({returncode}): {' '.join(cmd)}\n{stderr}")


class GitService:
    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd
        self._git_available = True

    def set_cwd(self, cwd: Path) -> None:
        self.cwd = cwd

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str] | None:
        argv = ["git", *args]
        try:
            return subprocess.run(argv, cwd=self.cwd, capture_output=True, text=True, timeout=5)
        except FileNotFoundError:
            if self._git_available:
                logger.warning("git executable not found on PATH")
                self._git_available = False
            return None
        except subprocess.TimeoutExpired:
            logger.warning("git command timed out: %s", argv)
            return None

    def is_git_repo(self) -> bool:
        result = self._run(["rev-parse", "--is-inside-work-tree"])
        if result is None:
            return False
        return result.returncode == 0

    def get_branch(self) -> GitBranchInfo:
        if not self.is_git_repo():
            return GitBranchInfo(is_git_repo=False)

        result = self._run(["branch", "--show-current"])
        if result is None:
            return GitBranchInfo(is_git_repo=True, branch=None, is_detached=True)
        if result.returncode != 0:
            raise GitCommandError(
                ["git", "branch", "--show-current"], result.returncode, result.stderr
            )

        branch = result.stdout.strip()
        return GitBranchInfo(is_git_repo=True, branch=branch or None, is_detached=not branch)

    def get_status(self) -> GitStatus:
        if not self.is_git_repo():
            return GitStatus(is_git_repo=False)

        result = self._run(["status", "--porcelain"])
        if result is None:
            return GitStatus(is_git_repo=True)
        if result.returncode != 0:
            raise GitCommandError(
                ["git", "status", "--porcelain"], result.returncode, result.stderr
            )

        staged: list[str] = []
        modified: list[str] = []
        untracked: list[str] = []
        for line in result.stdout.splitlines():
            if not line:
                continue
            index_status, worktree_status, path = line[0], line[1], line[3:]
            if index_status == "?":
                untracked.append(path)
                continue
            if index_status != " ":
                staged.append(path)
            if worktree_status != " ":
                modified.append(path)

        return GitStatus(is_git_repo=True, staged=staged, modified=modified, untracked=untracked)

    def get_recent_log(self, n: int = 5) -> list[str]:
        if not self.is_git_repo():
            return []

        result = self._run(["log", f"-n{n}", "--oneline"])
        if result is None:
            return []
        if result.returncode != 0:
            if "does not have any commits yet" in result.stderr:
                return []
            raise GitCommandError(
                ["git", "log", f"-n{n}", "--oneline"], result.returncode, result.stderr
            )

        return [line for line in result.stdout.splitlines() if line]
