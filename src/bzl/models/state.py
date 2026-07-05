from pydantic import BaseModel, Field


class AppState(BaseModel):
    active_project: str | None = None
    recent_projects: list[str] = Field(default_factory=list)
    theme: str = "textual-dark"
