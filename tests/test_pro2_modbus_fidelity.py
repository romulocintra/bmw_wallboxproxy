import struct
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import dr_client
from meter_models import build_inepro_pro2
from modbus_codec import append_crc, modbus_crc


def _f32(regs, addr):
    return struct.unpack(">f", struct.pack(">HH", regs[addr], regs[addr + 1]))[0]


def _pro2_supported_word_addresses():
    single = {
        0x4002, 0x4003, 0x4004, 0x400B, 0x400F, 0x4010, 0x4011,
        0x4012, 0x4015, 0x4016, 0x4017, 0x6048,
    }
    pairs = {
        0x4000, 0x4005, 0x4007, 0x4009, 0x400D, 0x401B, 0x401D,
        0x5000, 0x5002, 0x5008, 0x500A, 0x500C, 0x5012, 0x501A,
        0x5022, 0x502A, 0x6000, 0x6002, 0x6004, 0x600C, 0x600E,
        0x6010, 0x6018, 0x601A, 0x601C, 0x6024, 0x6026, 0x6028,
        0x6030, 0x6032, 0x6034, 0x603C, 0x603E, 0x6040, 0x6049,
    }
    words = set(single)
    for addr in pairs:
        words.update((addr, addr + 1))
    return words


def _pro380_only_word_addresses():
    pairs = {
        0x5004, 0x5006, 0x500E, 0x5010, 0x5014, 0x5016, 0x5018,
        0x501C, 0x501E, 0x5020, 0x5024, 0x5026, 0x5028, 0x502C,
        0x502E, 0x5030, 0x6006, 0x6008, 0x600A, 0x6012, 0x6014,
        0x6016, 0x601E, 0x6020, 0x6022, 0x602A, 0x602C, 0x602E,
        0x6036, 0x6038, 0x603A, 0x6042, 0x6044, 0x6046,
    }
    singles = {0x400C, 0x4013, 0x4014, 0x4018, 0x4019, 0x401A, 0x401F}
    words = set(singles)
    for addr in pairs:
        words.update((addr, addr + 1))
    return words


def test_pro2_exposes_exact_documented_word_map_only():
    regs = build_inepro_pro2({"u1": 230.0, "i1": 16.0, "p_total": 3.68}, "cdab")
    assert set(regs) == _pro2_supported_word_addresses()
    assert not (set(regs) & _pro380_only_word_addresses())


def test_pro2_float_encoding_is_always_abcd():
    regs = build_inepro_pro2(
        {"voltage_avg": 230.0, "u1": 230.0, "freq": 50.0, "current_total": 16.0,
         "i1": 16.0, "p_total": 3.68, "q_total": 0.0, "s_total": 3.68, "pf_total": 1.0},
        "cdab",
    )
    assert math_is_close(_f32(regs, 0x500C), 16.0)
    assert math_is_close(_f32(regs, 0x5012), 3.68)


def math_is_close(a, b):
    return abs(a - b) < 1e-6


def test_wallbox_current_request_and_pro2_response_vector(monkeypatch):
    request = bytes.fromhex("01 03 50 0C 00 02 15 08")
    expected_values = (0.0, 6.0, 10.0, 16.0, 20.0, 25.0, 32.0)

    for amps in expected_values:
        regs = build_inepro_pro2({"i1": amps}, "abcd")
        monkeypatch.setattr(dr_client, "get_register_map", lambda regs=regs: regs)
        response = dr_client.handle_rtu_request(request)
        assert response is not None
        assert response[:2] == b"\x01\x03"
        assert response[2] == 4
        assert _f32({0x500C: struct.unpack(">H", response[3:5])[0],
                     0x500D: struct.unpack(">H", response[5:7])[0]}, 0x500C) == amps
        assert response[-2:] == struct.pack("<H", modbus_crc(response[:-2]))


def test_wallbox_32a_response_matches_captured_frame(monkeypatch):
    regs = build_inepro_pro2({"i1": 32.0}, "abcd")
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)
    request = bytes.fromhex("01 03 50 0C 00 02 15 08")
    expected = bytes.fromhex("01 03 04 42 00 00 00 EE 4B")
    assert dr_client.handle_rtu_request(request) == expected


def test_documented_pro2_write_command_vectors_have_valid_modbus_crc():
    vectors = (
        "01 06 40 03 00 0A",
        "01 06 40 04 25 80",
        "01 10 40 0D 00 02 04 41 20 00 00",
        "01 06 40 0F 00 0A",
        "01 06 40 10 00 19",
        "01 06 40 11 00 02",
        "01 06 40 16 00 00",
        "01 06 60 48 00 02",
        "01 10 60 49 00 02 04 00 00 00 00",
    )
    for vector in vectors:
        frame = bytes.fromhex(vector)
        assert append_crc(frame)[:-2] == frame
        assert struct.unpack("<H", append_crc(frame)[-2:])[0] == modbus_crc(frame)
