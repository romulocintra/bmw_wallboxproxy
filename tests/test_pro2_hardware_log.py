import struct
import pytest
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
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "float32_abcd")
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
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "float32_abcd")
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

def test_live_capture_2026_09_16_500c_responses_are_float32_abcd():
    # Captured from the BMW Wallbox <-> proxy exchange on 2026-09-16.
    captured = [
        ("01 03 04 40 cd 1e b8 77 de", 6.41),
        ("01 03 04 40 c6 66 66 a4 44", 6.20),
        ("01 03 04 40 c4 cc cd 3a 9b", 6.15),
        ("01 03 04 40 c0 51 ec d3 d2", 6.01),
        ("01 03 04 40 be 14 7b c0 f4", 5.94),
        ("01 03 04 40 b8 a3 d7 57 78", 5.77),
        ("01 03 04 40 bb 85 1f bc 8e", 5.86),
        ("01 03 04 40 b0 f5 c3 e9 15", 5.53),
        ("01 03 04 40 b2 3d 71 9f 60", 5.57),
        ("01 03 04 40 bd c2 8f 6f 13", 5.93),
        ("01 03 04 40 ca e1 48 87 ab", 6.34),
    ]
    for frame_hex, expected in captured:
        frame = bytes.fromhex(frame_hex)
        assert len(frame) == 9
        assert frame[:3] == bytes.fromhex("01 03 04")
        assert append_crc(frame[:-2]) == frame
        assert struct.unpack(">f", frame[3:7])[0] == pytest.approx(expected, abs=0.01)
