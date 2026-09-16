import struct
import sys
from pathlib import Path

import pytest

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import config
import dr_client
from meter_models import build_inepro_pro2
import pro2_runtime_patch  # noqa: F401 - installs the PRO2 dispatcher patch
from modbus_codec import modbus_crc


def _request(start_addr: int, quantity: int) -> bytes:
    body = bytes([1, 3]) + struct.pack(">HH", start_addr, quantity)
    return body + struct.pack("<H", modbus_crc(body))


def _decode_cdab(payload: bytes) -> float:
    assert len(payload) == 4
    return struct.unpack(">f", payload[2:4] + payload[0:2])[0]


def _assert_exact_float_response(response: bytes, expected: float) -> None:
    assert response is not None
    assert len(response) == 9
    assert response[:3] == bytes.fromhex("01 03 04")
    assert _decode_cdab(response[3:7]) == pytest.approx(expected, abs=1e-5)
    assert response[-2:] == struct.pack("<H", modbus_crc(response[:-2]))


def test_delta_current_l1_500c_returns_exact_two_registers(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2(
        {"u1": 230.0, "i1": 20.0, "i2": 16.0, "i3": 12.0, "p_total": 4.5},
        "cdab",
    )
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)

    response = dr_client.handle_rtu_request(_request(0x500C, 2))

    _assert_exact_float_response(response, 20.0)
    assert response[3:7] == bytes.fromhex("00 00 41 A0")


def test_delta_current_l2_500e_returns_exact_two_registers(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2({"i1": 20.0, "i2": 16.0, "i3": 12.0}, "cdab")
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)

    response = dr_client.handle_rtu_request(_request(0x500E, 2))

    _assert_exact_float_response(response, 16.0)


def test_delta_current_l3_5010_returns_exact_two_registers(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2({"i1": 20.0, "i2": 16.0, "i3": 12.0}, "cdab")
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)

    response = dr_client.handle_rtu_request(_request(0x5010, 2))

    _assert_exact_float_response(response, 12.0)


def test_delta_voltage_l1_5000_returns_exact_two_registers(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2({"u1": 230.0}, "cdab")
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)

    response = dr_client.handle_rtu_request(_request(0x5000, 2))

    _assert_exact_float_response(response, 230.0)
    assert response[3:7] == bytes.fromhex("00 00 43 66")


def test_delta_active_power_5012_returns_exact_two_registers(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2({"p_total": 4.5}, "cdab")
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)

    response = dr_client.handle_rtu_request(_request(0x5012, 2))

    _assert_exact_float_response(response, 4.5)
