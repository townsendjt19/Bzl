from enum import StrEnum

from pydantic import BaseModel


class ProviderKind(StrEnum):
    OLLAMA = "ollama"
    CHATGPT = "chatgpt"
    CLAUDE_CODE = "claude_code"


class ProviderMessage(BaseModel):
    role: str
    content: str


class ProviderResponse(BaseModel):
    content: str
    provider: str
    stub: bool = True
