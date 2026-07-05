import pytest


@pytest.fixture
def tmp_configs_dir(tmp_path):
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    return configs_dir
