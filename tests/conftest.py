import importlib

import pytest


@pytest.fixture(autouse=True)
def reset_environment_config(monkeypatch):
    """Keep tests independent from a developer's local .env/environment."""
    keys = (
        "METER_MODEL",
        "TEST_MODE",
        "TEST_CURRENT_A",
        "TEST_VOLTAGE_V",
        "TEST_FREQUENCY_HZ",
        "TEST_POWER_FACTOR",
        "MODBUS_INEPRO_500C_ENCODING",
        "MODBUS_FLOAT_WORD_ORDER",
        "MODBUS_REGISTER_ALIAS_MODE",
        "POWER_OFFSET_WATTS",
    )
    for key in keys:
        monkeypatch.delenv(key, raising=False)

    import config
    import test_mode

    importlib.reload(config)
    importlib.reload(test_mode)
    yield
    importlib.reload(config)
    importlib.reload(test_mode)
