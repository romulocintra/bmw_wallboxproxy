import importlib

import config
import test_mode


def test_custom_test_values_override_sequence(monkeypatch):
    monkeypatch.setenv("TEST_CURRENT_A", "19.5")
    monkeypatch.setenv("TEST_VOLTAGE_V", "231.0")
    monkeypatch.setenv("TEST_FREQUENCY_HZ", "49.9")
    monkeypatch.setenv("TEST_POWER_FACTOR", "0.92")
    importlib.reload(config)
    importlib.reload(test_mode)

    values = test_mode.next_test_values()

    assert values["i1"] == 19.5
    assert values["i2"] == 19.5
    assert values["i3"] == 19.5
    assert values["u1"] == 231.0
    assert values["freq"] == 49.9
    assert values["pf1"] == 0.92
    assert values["p1"] == 231.0 * 19.5 / 1000.0 * 0.92
    assert values["s1"] == 231.0 * 19.5 / 1000.0


def test_unset_custom_current_keeps_sequence(monkeypatch):
    monkeypatch.delenv("TEST_CURRENT_A", raising=False)
    monkeypatch.delenv("TEST_VOLTAGE_V", raising=False)
    monkeypatch.delenv("TEST_FREQUENCY_HZ", raising=False)
    monkeypatch.delenv("TEST_POWER_FACTOR", raising=False)
    importlib.reload(config)
    importlib.reload(test_mode)
    test_mode.reset_test_sequence()

    values = test_mode.next_test_values()

    assert values["i1"] == 0.0
    assert values["u1"] == 230.0
    assert values["freq"] == 50.0
    assert values["pf1"] == 0.0
