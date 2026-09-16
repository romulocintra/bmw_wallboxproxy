import importlib
import config
import register_map


def test_alias_mode_does_not_overwrite_canonical_current(monkeypatch):
    monkeypatch.setenv("METER_MODEL", "inepro_pro2")
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("TEST_CURRENT_A", "19.32")
    monkeypatch.setenv("MODBUS_INEPRO_500C_ENCODING", "int32_ma_cdab")
    monkeypatch.setenv("MODBUS_REGISTER_ALIAS_MODE", "alias_both")
    importlib.reload(config)
    importlib.reload(register_map)
    regs = register_map.get_register_map()
    assert regs[0x500C] == 0x4B78
    assert regs[0x500D] == 0x0000
