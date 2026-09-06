import struct
import sys
from pathlib import Path

import pytest

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import config
import dr_client
import pro2_runtime_patch  # noqa: F401 - installs the PRO2 wrappers
from modbus_codec import append_crc, modbus_crc
from pro2_state import get_slave_id, reset_state, write_fc06
from register_map import get_register_map
from state import modbus_log, stats, stats_lock


@pytest.fixture(autouse=True)
def _reset_pro2_runtime_state():
    reset_state()
    with stats_lock:
        modbus_log.clear()
        stats["rx_frames"] = 0
        stats["tx_frames"] = 0
        stats["crc_fail"] = 0
        stats["wrong_slave"] = 0
        stats["last_fc"] = "-"
        stats["last_start_addr"] = "-"
        stats["last_quantity"] = "-"
    yield
    reset_state()


def _rtu(body: bytes) -> bytes:
    return append_crc(body)


def _f32(regs, addr):
    return struct.unpack(">f", struct.pack(">HH", regs[addr], regs[addr + 1]))[0]


def test_pro2_fc06_write_echoes_and_changes_readback(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")

    request = _rtu(bytes.fromhex("01 06 40 10 00 19"))
    response = dr_client.handle_rtu_request(request)
    assert response == request
    assert get_register_map()[0x4010] == 25


def test_pro2_fc06_invalid_address_returns_exception_02(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")

    request = _rtu(bytes.fromhex("01 06 50 04 00 00"))
    response = dr_client.handle_rtu_request(request)
    assert response[:3] == bytes.fromhex("01 86 02")
    assert response[-2:] == struct.pack("<H", modbus_crc(response[:-2]))


def test_pro2_fc16_float_write_changes_readback(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")

    request = _rtu(bytes.fromhex("01 10 40 0D 00 02 04 41 20 00 00"))
    response = dr_client.handle_rtu_request(request)
    assert response == _rtu(bytes.fromhex("01 10 40 0D 00 02"))
    assert abs(_f32(get_register_map(), 0x400D) - 10.0) < 1e-6


def test_pro2_fc16_invalid_address_returns_exception_02(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")

    request = _rtu(bytes.fromhex("01 10 50 04 00 02 04 00 00 00 00"))
    response = dr_client.handle_rtu_request(request)
    assert response[:3] == bytes.fromhex("01 90 02")
    assert response[-2:] == struct.pack("<H", modbus_crc(response[:-2]))


def test_pro2_invalid_read_returns_exception_02(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")

    request = _rtu(bytes.fromhex("01 03 50 04 00 02"))
    response = dr_client.handle_rtu_request(request)
    assert response[:3] == bytes.fromhex("01 83 02")
    assert response[-2:] == struct.pack("<H", modbus_crc(response[:-2]))


def test_pro2_modbus_id_write_changes_active_slave(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")
    write_fc06(0x4003, 10)
    assert get_slave_id() == 10

    request = _rtu(bytes.fromhex("0A 03 50 0C 00 02"))
    response = dr_client.handle_rtu_request(request)
    assert response is not None
    assert response[:3] == bytes.fromhex("0A 03 04")


def test_pro2_fc16_bad_float_request_returns_exception_03(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")

    # 400D is a two-word FLOAT32 register; quantity=1 is not a valid write.
    request = _rtu(bytes.fromhex("01 10 40 0D 00 01 02 00 00"))
    response = dr_client.handle_rtu_request(request)
    assert response[:3] == bytes.fromhex("01 90 03")


def test_pro2_request_is_visible_in_modbus_activity(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")

    request = _rtu(bytes.fromhex("01 03 50 0C 00 02"))
    response = dr_client.handle_rtu_request(request)

    assert response[:4] == bytes.fromhex("01 03 04 40")
    with stats_lock:
        entries = list(modbus_log)
        snapshot = stats.copy()
    assert any("RX RTU" in entry for entry in entries)
    assert any("DEC mode=rtu_over_tcp" in entry for entry in entries)
    assert any("MAP slave=1 fc=3 addr=0x500C-0x500D" in entry for entry in entries)
    assert snapshot["rx_frames"] == 1
    assert snapshot["last_fc"] == 3
    assert snapshot["last_start_addr"] == "0x500C"
    assert snapshot["last_quantity"] == 2


def test_pro2_current_alias_registers_are_both_available(monkeypatch):
    monkeypatch.setattr(config, "get_meter_model", lambda: "inepro_pro2")
    regs = get_register_map()
    assert 0x500A in regs
    assert 0x500C in regs
