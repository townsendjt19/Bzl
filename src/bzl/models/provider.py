from enum import StrEnum

from pydantic import BaseModel, Field


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


class OllamaConfig(BaseModel):
    host: str = "http://localhost:11434"
    model: str = "llama3"


class ClaudeCodeConfig(BaseModel):
    command: str = "claude"


class ProvidersConfig(BaseModel):
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    claude_code: ClaudeCodeConfig = Field(default_factory=ClaudeCodeConfig)
