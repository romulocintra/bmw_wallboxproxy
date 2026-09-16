import importlib
import config
import register_map


def _reload_with(monkeypatch, encoding, current=19.32):
    monkeypatch.setenv("METER_MODEL", "inepro_pro2")
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("TEST_CURRENT_A", str(current))
    monkeypatch.setenv("MODBUS_INEPRO_500C_ENCODING", encoding)
    importlib.reload(config)
    importlib.reload(register_map)


def test_int32_ma_cdab_is_explicit_word_swap(monkeypatch):
    _reload_with(monkeypatch, "int32_ma_cdab")
    regs = register_map.get_register_map()
    assert regs[0x500C] == 0x4B78
    assert regs[0x500D] == 0x0000


def test_int32_ma_abcd_is_explicit_no_swap(monkeypatch):
    _reload_with(monkeypatch, "int32_ma_abcd")
    regs = register_map.get_register_map()
    assert regs[0x500C] == 0x0000
    assert regs[0x500D] == 0x4B78


def test_int32_encoding_is_independent_of_float_word_order(monkeypatch):
    _reload_with(monkeypatch, "int32_ma_cdab")
    monkeypatch.setenv("MODBUS_FLOAT_WORD_ORDER", "abcd")
    importlib.reload(config)
    importlib.reload(register_map)
    regs = register_map.get_register_map()
    assert regs[0x500C] == 0x4B78
    assert regs[0x500D] == 0x0000
