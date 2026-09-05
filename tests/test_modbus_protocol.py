import struct
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import config
import dr_client
import register_map
from modbus_codec import append_crc, modbus_crc


def _request(slave, function_code, start_addr, quantity):
    body = struct.pack(">BBHH", slave, function_code, start_addr, quantity)
    return append_crc(body)


def _response_words(frame):
    assert modbus_crc(frame[:-2]) == struct.unpack("<H", frame[-2:])[0]
    assert frame[1] in (3, 4)
    byte_count = frame[2]
    assert byte_count == len(frame) - 5
    return [struct.unpack(">H", frame[i:i + 2])[0] for i in range(3, 3 + byte_count, 2)]


def _set_values(monkeypatch, meter_model):
    monkeypatch.setattr(config, "METER_MODEL", meter_model)
    monkeypatch.setattr(register_map, "latest_values", {
        "u1": 230.0,
        "u2": 0.0,
        "u3": 0.0,
        "i1": 16.21,
        "i2": 0.0,
        "i3": 0.0,
        "p_total": 3728.5,
        "p1": 3728.5,
        "p2": 0.0,
        "p3": 0.0,
        "freq": 50.0,
        "e_import_total": 100.0,
        "e_export_total": 2.0,
        "power_offset": 0.0,
    })


def test_rtu_over_tcp_pro380_returns_valid_float_response(monkeypatch):
    _set_values(monkeypatch, "inepro_pro380")

    request = _request(1, 3, 0x500C, 2)
    response = dr_client.handle_rtu_request(request)

    assert response is not None
    assert response[0:2] == bytes([1, 3])
    words = _response_words(response)
    raw = struct.pack(">HH", *words)
    assert abs(struct.unpack(">f", raw)[0] - 16.21) < 1e-5


def test_rtu_over_tcp_pro2_is_single_phase(monkeypatch):
    _set_values(monkeypatch, "inepro_pro2")

    l1 = dr_client.handle_rtu_request(_request(1, 3, 0x500C, 2))
    l2 = dr_client.handle_rtu_request(_request(1, 3, 0x500E, 2))

    assert l1 is not None and l2 is not None
    assert abs(struct.unpack(">f", struct.pack(">HH", *_response_words(l1)))[0] - 16.21) < 1e-5
    assert struct.pack(">HH", *_response_words(l2)) == struct.pack(">f", 0.0)


def test_rtu_crc_invalid_frame_is_dropped(monkeypatch):
    _set_values(monkeypatch, "inepro_pro380")

    request = bytearray(_request(1, 3, 0x500C, 2))
    request[-1] ^= 0xFF

    assert dr_client.handle_rtu_request(bytes(request)) is None


def test_wrong_slave_is_ignored(monkeypatch):
    _set_values(monkeypatch, "inepro_pro380")

    request = _request(2, 3, 0x500C, 2)
    assert dr_client.handle_rtu_request(request) is None
