import os
import struct


def modbus_crc(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def _raw_test_response(data: bytes) -> bytes | None:
    """Return the configured raw RTU response body when this is a test response."""
    test_mode = os.environ.get("TEST_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    enabled = os.environ.get("TEST_RAW_RESPONSE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    raw = os.environ.get("TEST_RAW_RESPONSE", "").strip()
    if not test_mode or not enabled or not raw:
        return None

    # A normal read response is [slave, function, byte_count, data...].
    # Requests do not match this shape, so request CRC generation remains safe
    # even when raw-response testing is enabled in the add-on process.
    if len(data) < 3 or data[1] not in (3, 4) or data[2] != len(data) - 3:
        return None

    try:
        body = bytes.fromhex(raw)
    except ValueError as exc:
        raise ValueError("TEST_RAW_RESPONSE must contain hexadecimal bytes") from exc

    if len(body) < 3 or body[1] not in (3, 4):
        raise ValueError("TEST_RAW_RESPONSE must start with slave id and function code 03 or 04")
    if body[2] != len(body) - 3:
        raise ValueError("TEST_RAW_RESPONSE byte count does not match payload length")
    if body[2] % 2:
        raise ValueError("TEST_RAW_RESPONSE byte count must be even for register reads")

    return body


def append_crc(data: bytes) -> bytes:
    raw_body = _raw_test_response(data)
    if raw_body is not None:
        data = raw_body
    return data + struct.pack("<H", modbus_crc(data))


def check_crc(frame: bytes) -> bool:
    if len(frame) < 4:
        return False
    body = frame[:-2]
    recv_crc = struct.unpack("<H", frame[-2:])[0]
    return recv_crc == modbus_crc(body)


def exception_response(slave_id: int, function_code: int, exc_code: int) -> bytes:
    return append_crc(bytes([slave_id, function_code | 0x80, exc_code]))


# IEEE754 single precision cannot represent everything a Home Assistant sensor
# may report. struct.pack(">f", ...) raises OverflowError outside this range and
# a single bad reading would otherwise make every register build fail.
FLOAT32_MAX = 3.4028234663852886e38


def to_float32_safe(value: float) -> float:
    """Coerce any numeric input into a value struct.pack(">f") accepts."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0

    if number != number:  # NaN
        return 0.0
    if number > FLOAT32_MAX:
        return FLOAT32_MAX
    if number < -FLOAT32_MAX:
        return -FLOAT32_MAX
    return number


def float_to_abcd_words(value: float) -> tuple[int, int]:
    packed = struct.pack(">f", to_float32_safe(value))
    return struct.unpack(">HH", packed)


def float_to_words(value: float, word_order: str = "abcd") -> tuple[int, int]:
    hi, lo = float_to_abcd_words(value)
    if word_order == "cdab":
        return lo, hi
    return hi, lo
