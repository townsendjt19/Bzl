from bzl.config.loader import load_state, save_state
from bzl.models.state import AppState
from bzl.services.state_service import StateService


def test_record_project_switch_sets_active_and_recent(tmp_path):
    service = StateService(AppState(), tmp_path / "state.local.yaml")
    service.record_project_switch("alpha")
    assert service.state.active_project == "alpha"
    assert service.state.recent_projects == ["alpha"]


def test_record_project_switch_dedups_and_moves_to_front(tmp_path):
    service = StateService(AppState(), tmp_path / "state.local.yaml")
    service.record_project_switch("alpha")
    service.record_project_switch("beta")
    service.record_project_switch("alpha")
    assert service.state.recent_projects == ["alpha", "beta"]


def test_record_project_switch_caps_recent_list(tmp_path):
    service = StateService(AppState(), tmp_path / "state.local.yaml")
    for name in ["a", "b", "c", "d", "e", "f"]:
        service.record_project_switch(name)
    assert service.state.recent_projects == ["f", "e", "d", "c", "b"]


def test_set_theme_updates_state(tmp_path):
    service = StateService(AppState(), tmp_path / "state.local.yaml")
    service.set_theme("nord")
    assert service.state.theme == "nord"


def test_mutations_are_persisted_to_disk(tmp_path):
    path = tmp_path / "state.local.yaml"
    service = StateService(AppState(), path)
    service.record_project_switch("alpha")
    service.set_theme("nord")

    reloaded = load_state(path)
    assert reloaded.active_project == "alpha"
    assert reloaded.recent_projects == ["alpha"]
    assert reloaded.theme == "nord"


def test_load_state_missing_file_returns_default(tmp_path):
    state = load_state(tmp_path / "state.local.yaml")
    assert state == AppState()


def test_save_state_round_trips(tmp_path):
    path = tmp_path / "state.local.yaml"
    state = AppState(active_project="demo", recent_projects=["demo"], theme="gruvbox")
    save_state(path, state)
    assert load_state(path) == state
