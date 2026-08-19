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


def append_crc(data: bytes) -> bytes:
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