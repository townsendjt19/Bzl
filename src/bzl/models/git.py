from pydantic import BaseModel, Field


class GitBranchInfo(BaseModel):
    is_git_repo: bool
    branch: str | None = None
    is_detached: bool = False


class GitStatus(BaseModel):
    is_git_repo: bool
    staged: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)
    untracked: list[str] = Field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not (self.staged or self.modified or self.untracked)
