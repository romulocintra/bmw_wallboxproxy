import struct
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from modbus_codec import (
    append_crc,
    check_crc,
    exception_response,
    float_to_words,
    modbus_crc,
    to_float32_safe,
)


def test_modbus_crc_known_request():
    frame = bytes.fromhex("01 03 50 0C 00 02")
    assert modbus_crc(frame) == 0x0815
    assert append_crc(frame) == bytes.fromhex("01 03 50 0C 00 02 15 08")


def test_crc_validation_rejects_corruption():
    frame = append_crc(bytes.fromhex("01 03 50 0C 00 02"))
    assert check_crc(frame)

    corrupted = bytearray(frame)
    corrupted[3] ^= 0x01
    assert not check_crc(bytes(corrupted))


def test_float_word_orders_are_explicit():
    value = 16.21
    abcd = float_to_words(value, "abcd")
    cdab = float_to_words(value, "cdab")

    assert cdab == (abcd[1], abcd[0])
    assert struct.unpack(">f", struct.pack(">HH", *abcd))[0] == value


def test_float32_safe_clamps_invalid_values():
    assert to_float32_safe(float("nan")) == 0.0
    assert to_float32_safe(1e100) < 1e39
    assert to_float32_safe(-1e100) > -1e39
    assert to_float32_safe("not-a-number") == 0.0


def test_exception_response_is_valid_modbus_rtu():
    response = exception_response(1, 3, 2)
    assert response == bytes.fromhex("01 83 02 C0 F1")
    assert check_crc(response)
