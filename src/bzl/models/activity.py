from pydantic import BaseModel


class ActivityLogEntry(BaseModel):
    timestamp: str
    source: str
    message: str
    level: str = "info"
