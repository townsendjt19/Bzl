import os
from pathlib import Path


def resolve_configs_dir() -> Path:
    """Resolve the directory containing projects.yaml / projects.local.yaml.

    Order: BZL_CONFIG_DIR env var > a configs/ directory found by walking
    up from this file's location (repo-relative dev run) > cwd/configs.
    """
    env_dir = os.environ.get("BZL_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)

    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "configs"
        if candidate.is_dir():
            return candidate

    return Path.cwd() / "configs"


def resolve_state_file() -> Path:
    """Resolve the path to the gitignored local state file (recent projects, theme, ...)."""
    return resolve_configs_dir() / "state.local.yaml"
