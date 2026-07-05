from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from bzl.models.conversation import ConversationsFile
from bzl.models.project import ProjectConfig, ProjectsFile
from bzl.models.provider import ProvidersConfig
from bzl.models.state import AppState


class ConfigError(Exception):
    """Raised for any problem loading or validating Bzl config files."""


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"expected a mapping at the top level of {path}")
    return data


def load_projects_file(path: Path) -> ProjectsFile:
    """Load and validate the committed projects.yaml. Secrets are not allowed here."""
    data = _read_yaml(path)
    for entry in data.get("projects", []):
        if isinstance(entry, dict) and entry.get("environment"):
            raise ConfigError(
                f"{path} must not set 'environment' for project "
                f"{entry.get('name', '<unknown>')!r} — use projects.local.yaml instead"
            )
    try:
        return ProjectsFile.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"invalid projects file {path}: {exc}") from exc


def load_local_overrides(path: Path) -> dict[str, dict[str, str]]:
    """Load the gitignored local overlay, keyed by project name -> environment dict.

    Missing file means "no overrides" — this is not an error.
    """
    if not path.exists():
        return {}
    data = _read_yaml(path)
    overrides: dict[str, dict[str, str]] = {}
    for name, entry in data.get("projects", {}).items():
        if not isinstance(entry, dict):
            raise ConfigError(f"{path}: entry for {name!r} must be a mapping")
        unexpected = set(entry.keys()) - {"environment"}
        if unexpected:
            raise ConfigError(
                f"{path}: project {name!r} may only set 'environment', got extra keys {unexpected}"
            )
        overrides[name] = dict(entry.get("environment", {}))
    return overrides


def load_merged_projects(configs_dir: Path) -> ProjectsFile:
    """Load projects.yaml and merge in environment overrides from projects.local.yaml."""
    projects_file = load_projects_file(configs_dir / "projects.yaml")
    overrides = load_local_overrides(configs_dir / "projects.local.yaml")

    merged: list[ProjectConfig] = []
    for project in projects_file.projects:
        env = overrides.get(project.name, {})
        merged.append(project.model_copy(update={"environment": env}))
    return ProjectsFile(projects=merged)


def load_state(path: Path) -> AppState:
    """Load the gitignored local state file. Missing file means default state."""
    if not path.exists():
        return AppState()
    data = _read_yaml(path)
    try:
        return AppState.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"invalid state file {path}: {exc}") from exc


def save_state(path: Path, state: AppState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(state.model_dump()), encoding="utf-8")


def load_providers_config(path: Path) -> ProvidersConfig:
    """Load the committed providers.yaml. Missing file means all-default config."""
    if not path.exists():
        return ProvidersConfig()
    data = _read_yaml(path)
    try:
        return ProvidersConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"invalid providers config {path}: {exc}") from exc


def load_conversations(path: Path) -> ConversationsFile:
    """Load the gitignored local conversation history file. Missing file means no history."""
    if not path.exists():
        return ConversationsFile()
    data = _read_yaml(path)
    try:
        return ConversationsFile.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"invalid conversations file {path}: {exc}") from exc


def save_conversations(path: Path, conversations: ConversationsFile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(conversations.model_dump()), encoding="utf-8")
