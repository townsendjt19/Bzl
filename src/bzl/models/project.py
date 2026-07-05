from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str
    description: str = ""
    path: str
    tags: list[str] = Field(default_factory=list)
    startup_commands: list[str] = Field(default_factory=list)
    preferred_provider: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)


class ProjectsFile(BaseModel):
    projects: list[ProjectConfig] = Field(default_factory=list)
