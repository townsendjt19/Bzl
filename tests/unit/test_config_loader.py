import pytest

from bzl.config.loader import (
    ConfigError,
    load_local_overrides,
    load_merged_projects,
    load_projects_file,
    load_providers_config,
)

PROJECTS_YAML = """
projects:
  - name: alpha
    description: Alpha project
    path: /tmp/alpha
    tags: [python]
    preferred_provider: ollama
  - name: beta
    path: /tmp/beta
"""

LOCAL_YAML = """
projects:
  alpha:
    environment:
      API_KEY: secret123
"""


def test_load_projects_file_parses_valid_yaml(tmp_configs_dir):
    path = tmp_configs_dir / "projects.yaml"
    path.write_text(PROJECTS_YAML, encoding="utf-8")

    result = load_projects_file(path)

    assert len(result.projects) == 2
    assert result.projects[0].name == "alpha"
    assert result.projects[0].tags == ["python"]
    assert result.projects[1].environment == {}


def test_load_projects_file_missing_file_raises(tmp_configs_dir):
    with pytest.raises(ConfigError):
        load_projects_file(tmp_configs_dir / "projects.yaml")


def test_load_projects_file_rejects_environment_in_committed_file(tmp_configs_dir):
    path = tmp_configs_dir / "projects.yaml"
    path.write_text(
        """
projects:
  - name: alpha
    path: /tmp/alpha
    environment:
      LEAKED: yes
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_projects_file(path)


def test_load_local_overrides_missing_file_returns_empty(tmp_configs_dir):
    assert load_local_overrides(tmp_configs_dir / "projects.local.yaml") == {}


def test_load_local_overrides_rejects_unexpected_keys(tmp_configs_dir):
    path = tmp_configs_dir / "projects.local.yaml"
    path.write_text(
        """
projects:
  alpha:
    path: /somewhere/else
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_local_overrides(path)


def test_load_merged_projects_applies_environment_override(tmp_configs_dir):
    (tmp_configs_dir / "projects.yaml").write_text(PROJECTS_YAML, encoding="utf-8")
    (tmp_configs_dir / "projects.local.yaml").write_text(LOCAL_YAML, encoding="utf-8")

    merged = load_merged_projects(tmp_configs_dir)

    alpha = next(p for p in merged.projects if p.name == "alpha")
    beta = next(p for p in merged.projects if p.name == "beta")
    assert alpha.environment == {"API_KEY": "secret123"}
    assert beta.environment == {}


def test_load_merged_projects_without_local_file(tmp_configs_dir):
    (tmp_configs_dir / "projects.yaml").write_text(PROJECTS_YAML, encoding="utf-8")

    merged = load_merged_projects(tmp_configs_dir)

    assert all(p.environment == {} for p in merged.projects)


def test_load_providers_config_missing_file_returns_defaults(tmp_configs_dir):
    config = load_providers_config(tmp_configs_dir / "providers.yaml")
    assert config.ollama.host == "http://localhost:11434"
    assert config.ollama.model == "llama3"
    assert config.claude_code.command == "claude"


def test_load_providers_config_parses_overrides(tmp_configs_dir):
    path = tmp_configs_dir / "providers.yaml"
    path.write_text(
        """
ollama:
  host: http://example.local:11434
  model: mistral
claude_code:
  command: my-claude
""",
        encoding="utf-8",
    )

    config = load_providers_config(path)
    assert config.ollama.host == "http://example.local:11434"
    assert config.ollama.model == "mistral"
    assert config.claude_code.command == "my-claude"
