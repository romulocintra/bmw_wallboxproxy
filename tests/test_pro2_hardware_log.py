import struct
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import config
import register_map
from modbus_codec import append_crc


def _f32(regs, addr):
    return struct.unpack(">f", struct.pack(">HH", regs[addr], regs[addr + 1]))[0]


def test_capture_request_is_documented_pro2_l1_current():
    request = bytes.fromhex("01 03 50 0C 00 02 15 08")
    assert request == append_crc(bytes.fromhex("01 03 50 0C 00 02"))


def test_capture_response_values_match_test_mode_sequence(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    monkeypatch.setattr(register_map, "get_register_alias_mode", lambda: "exact")
    monkeypatch.setattr(register_map, "get_float_word_order", lambda: "abcd")
    monkeypatch.setattr(register_map, "get_power_offset_override", lambda: None)
    monkeypatch.setattr(register_map, "get_test_mode", lambda: True)

    from test_mode import reset_test_sequence
    reset_test_sequence()
    expected = (0.0, 6.0, 10.0, 16.0, 20.0, 25.0, 32.0, 25.0, 20.0, 16.0, 10.0, 6.0)
    observed = []
    for _ in expected:
        regs = register_map.get_register_map()
        observed.append(_f32(regs, 0x500C))
    assert tuple(observed) == expected


def test_capture_32a_response_is_exact_float32_abcd(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    monkeypatch.setattr(register_map, "get_register_alias_mode", lambda: "exact")
    monkeypatch.setattr(register_map, "get_float_word_order", lambda: "abcd")
    monkeypatch.setattr(register_map, "get_power_offset_override", lambda: None)
    monkeypatch.setattr(register_map, "get_test_mode", lambda: True)

    from test_mode import reset_test_sequence
    reset_test_sequence()
    for _ in range(6):
        register_map.get_register_map()
    regs = register_map.get_register_map()
    assert regs[0x500C] == 0x4200
    assert regs[0x500D] == 0x0000
    assert _f32(regs, 0x500C) == 32.0
