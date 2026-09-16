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
from register_map import _apply_inepro_current_encoding


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


def _assert_exact_response(response: bytes, payload: bytes) -> None:
    assert response is not None
    assert len(response) == 9
    assert response[:3] == bytes.fromhex("01 03 04")
    assert response[3:7] == payload
    assert response[-2:] == struct.pack("<H", modbus_crc(response[:-2]))


def _delta_regs(monkeypatch, values):
    monkeypatch.setattr(config, "METER_MODEL", "inepro_pro2")
    regs = build_inepro_pro2(values, "cdab")
    regs = _apply_inepro_current_encoding(regs, values)
    monkeypatch.setattr(dr_client, "get_register_map", lambda: regs)
    return regs


def test_delta_current_l1_500c_default_int32_milliamps_cdab(monkeypatch):
    values = {"u1": 230.0, "i1": 19.5, "i2": 16.0, "i3": 12.0, "p_total": 4.5}
    _delta_regs(monkeypatch, values)

    response = dr_client.handle_rtu_request(_request(0x500C, 2))

    # 19.5 A -> 19500 mA -> Int32 ABCD 00 00 4C 2C -> CDAB 4C 2C 00 00.
    _assert_exact_response(response, bytes.fromhex("4C 2C 00 00"))


def test_delta_current_l1_500c_float32_cdab(monkeypatch):
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "float32_cdab")
    values = {"i1": 20.0}
    _delta_regs(monkeypatch, values)

    response = dr_client.handle_rtu_request(_request(0x500C, 2))

    _assert_exact_float_response(response, 20.0)
    assert response[3:7] == bytes.fromhex("00 00 41 A0")


def test_delta_current_l1_500c_float32_cdab_is_independent_of_global_word_order(monkeypatch):
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "float32_cdab")
    monkeypatch.setattr(config, "MODBUS_FLOAT_WORD_ORDER", "abcd")
    values = {"i1": 20.0}
    _delta_regs(monkeypatch, values)

    response = dr_client.handle_rtu_request(_request(0x500C, 2))

    _assert_exact_float_response(response, 20.0)
    assert response[3:7] == bytes.fromhex("00 00 41 A0")


def test_delta_current_l1_500c_float32_abcd(monkeypatch):
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "float32_abcd")
    values = {"i1": 20.0}
    _delta_regs(monkeypatch, values)

    response = dr_client.handle_rtu_request(_request(0x500C, 2))

    _assert_exact_response(response, bytes.fromhex("41 A0 00 00"))


def test_delta_current_l2_500e_uses_selected_encoding(monkeypatch):
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "int32_ma_cdab")
    values = {"i1": 20.0, "i2": 16.0, "i3": 12.0}
    _delta_regs(monkeypatch, values)

    response = dr_client.handle_rtu_request(_request(0x500E, 2))

    # 16 A -> 16000 mA -> 0x00003E80 -> CDAB 3E 80 00 00.
    _assert_exact_response(response, bytes.fromhex("3E 80 00 00"))


def test_delta_current_l3_5010_uses_selected_encoding(monkeypatch):
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "int32_ma_cdab")
    values = {"i1": 20.0, "i2": 16.0, "i3": 12.0}
    _delta_regs(monkeypatch, values)

    response = dr_client.handle_rtu_request(_request(0x5010, 2))

    # 12 A -> 12000 mA -> 0x00002EE0 -> CDAB 2E E0 00 00.
    _assert_exact_response(response, bytes.fromhex("2E E0 00 00"))


def test_delta_voltage_l1_5000_remains_float32_cdab(monkeypatch):
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "int32_ma_cdab")
    values = {"u1": 230.0}
    _delta_regs(monkeypatch, values)

    response = dr_client.handle_rtu_request(_request(0x5000, 2))

    _assert_exact_float_response(response, 230.0)
    assert response[3:7] == bytes.fromhex("00 00 43 66")


def test_delta_active_power_5012_remains_float32_cdab(monkeypatch):
    monkeypatch.setattr(config, "MODBUS_INEPRO_500C_ENCODING", "int32_ma_cdab")
    values = {"p_total": 4.5}
    _delta_regs(monkeypatch, values)

    response = dr_client.handle_rtu_request(_request(0x5012, 2))

    _assert_exact_float_response(response, 4.5)
