import importlib

import pytest

import config


def test_meter_model_is_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("METER_MODEL", "inepro_pro2")
    reloaded = importlib.reload(config)
    assert reloaded.get_meter_model() == "inepro_pro2"


def test_meter_model_supports_all_profiles(monkeypatch):
    for model in ("inepro_pro380", "inepro_pro2", "janitza_b23"):
        monkeypatch.setenv("METER_MODEL", model)
        reloaded = importlib.reload(config)
        assert reloaded.get_meter_model() == model


def test_invalid_meter_model_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("METER_MODEL", "unsupported")
    reloaded = importlib.reload(config)
    assert reloaded.get_meter_model() == "inepro_pro380"


def test_meter_model_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("METER_MODEL", raising=False)
    reloaded = importlib.reload(config)
    assert reloaded.get_meter_model() == "inepro_pro380"


def test_addon_configuration_contains_meter_model_mapping():
    run_script = open("bmw_wallboxproxy/run.sh", encoding="utf-8").read()
    assert "export METER_MODEL=\"$(bashio::config 'meter_model')\"" in run_script


def test_addon_configuration_contains_test_mode_mapping():
    run_script = open("bmw_wallboxproxy/run.sh", encoding="utf-8").read()
    assert "export TEST_MODE=\"$(bashio::config 'test_mode')\"" in run_script


def test_addon_schema_lists_all_supported_meter_models():
    addon_config = open("bmw_wallboxproxy/config.yaml", encoding="utf-8").read()
    assert 'meter_model: "list(inepro_pro380|inepro_pro2|janitza_b23)"' in addon_config


def test_addon_schema_exposes_test_mode():
    addon_config = open("bmw_wallboxproxy/config.yaml", encoding="utf-8").read()
    assert 'test_mode: "bool"' in addon_config


@pytest.fixture(autouse=True)
def restore_config_module(monkeypatch):
    yield
    monkeypatch.delenv("METER_MODEL", raising=False)
    importlib.reload(config)
