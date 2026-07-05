from pydantic import BaseModel, Field


class MemoryFile(BaseModel):
    """Maps project name -> its persisted AI memory notes."""

    notes: dict[str, list[str]] = Field(default_factory=dict)
