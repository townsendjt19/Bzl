# Bzl

A terminal-first developer command center for managing projects, git workflows, and AI providers — built with [Textual](https://textual.textualize.io/).

Bzl is not a chatbot. It's a structured operating environment for developers: a dashboard showing your active project, git state, and available AI providers, driven by a small extensible command system.

## Status

v0.1 — foundation scaffold. AI providers are stubs (no real API calls yet). Plugin system is interfaces only (no runtime loading yet).

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv python install 3.12
uv sync
```

## Run

```bash
uv run bzl
```

## Develop

```bash
uv run pytest
uv run ruff check .
uv run black --check .
uv run mypy src
```

## Configuration

Projects are defined in `configs/projects.yaml` (committed, no secrets). Per-project environment variables/secrets go in `configs/projects.local.yaml` (gitignored) — copy `configs/projects.local.yaml.example` to get started.

## Architecture

```
src/bzl/
├── models/     pydantic data classes only, no logic
├── config/     YAML loading + validation
├── services/   business logic — ProjectService, GitService, ProviderRegistry
├── providers/  async AI provider interface + stubs (isolated from services/UI)
├── commands/   custom command registry (help, status, projects, git, ...)
├── core/       bootstrapping — wires everything together, no business logic
├── ui/         Textual screens/widgets — presentational only
└── plugins/    future extension points (interfaces only, no loader yet)
```

See `docs/` for more detail (added as the project grows).

## Roadmap

- Real AI provider integrations (Ollama, ChatGPT, Claude Code)
- Plugin runtime loading
- Automation workflows
- File-based logging
