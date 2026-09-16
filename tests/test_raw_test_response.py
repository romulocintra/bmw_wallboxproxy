import struct
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import dr_client
import modbus_codec
from modbus_codec import append_crc, modbus_crc


def _request(slave=1, function_code=3, start_addr=0x500C, quantity=2):
    return append_crc(struct.pack(">BBHH", slave, function_code, start_addr, quantity))


def test_raw_response_replaces_generated_rtu_response(monkeypatch):
    monkeypatch.setenv("TEST_RAW_RESPONSE_ENABLED", "true")
    monkeypatch.setenv("TEST_RAW_RESPONSE", "01 03 04 00 00 4B 78")

    response = dr_client.handle_rtu_request(_request())

    assert response is not None
    assert response[:-2] == bytes.fromhex("01 03 04 00 00 4B 78")
    assert response[-2:] == struct.pack("<H", modbus_crc(response[:-2]))


def test_raw_response_does_not_replace_when_disabled(monkeypatch):
    monkeypatch.setenv("TEST_RAW_RESPONSE_ENABLED", "false")
    monkeypatch.setenv("TEST_RAW_RESPONSE", "01 03 04 00 00 4B 78")

    response = dr_client.handle_rtu_request(_request())

    assert response is not None
    assert response[:-2] != bytes.fromhex("01 03 04 00 00 4B 78")


def test_raw_response_does_not_replace_modbus_requests(monkeypatch):
    monkeypatch.setenv("TEST_RAW_RESPONSE_ENABLED", "true")
    monkeypatch.setenv("TEST_RAW_RESPONSE", "01 03 04 00 00 4B 78")

    request = _request()
    assert request == bytes.fromhex("01 03 50 0C 00 02") + request[-2:]


def test_raw_response_rejects_invalid_hex(monkeypatch):
    monkeypatch.setenv("TEST_RAW_RESPONSE_ENABLED", "true")
    monkeypatch.setenv("TEST_RAW_RESPONSE", "01 03 04 ZZ")

    try:
        append_crc(bytes.fromhex("01 03 04 00 00 00 00"))
    except ValueError as exc:
        assert "hexadecimal" in str(exc)
    else:
        raise AssertionError("invalid raw response should fail")


def test_raw_response_rejects_mismatched_byte_count(monkeypatch):
    monkeypatch.setenv("TEST_RAW_RESPONSE_ENABLED", "true")
    monkeypatch.setenv("TEST_RAW_RESPONSE", "01 03 06 00 00 4B 78")

    try:
        append_crc(bytes.fromhex("01 03 04 00 00 00 00"))
    except ValueError as exc:
        assert "byte count" in str(exc)
    else:
        raise AssertionError("mismatched byte count should fail")
