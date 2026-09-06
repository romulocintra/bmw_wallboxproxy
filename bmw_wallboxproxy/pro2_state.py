"""Runtime configuration/state for the Inepro PRO2-Mod emulator."""

from threading import Lock
from typing import Dict, Tuple

_lock = Lock()

_config = {
    0x4003: 1,
    0x4004: 9600,
    0x400D: 1000.0,
    0x400F: 1,
    0x4010: 10,
    0x4011: 1,
    0x4016: 0,
    0x6048: 1,
    0x6049: 0.0,
}

_FC06_REGS = {0x4003, 0x4004, 0x400F, 0x4010, 0x4011, 0x4016, 0x6048}
_FC10_FLOAT_REGS = {0x400D, 0x6049}
_S0_RATES = (10000.0, 2000.0, 1000.0, 100.0, 10.0, 1.0, 0.1, 0.01)


def supported_fc06(addr: int) -> bool:
    return addr in _FC06_REGS


def supported_fc10(addr: int, quantity: int) -> bool:
    return quantity == 2 and addr in _FC10_FLOAT_REGS


def get_register(addr: int):
    with _lock:
        return _config.get(addr)


def snapshot() -> Dict[int, object]:
    with _lock:
        return dict(_config)


def get_slave_id(default: int = 1) -> int:
    with _lock:
        return int(_config.get(0x4003, default))


def write_fc06(addr: int, value: int) -> None:
    if not supported_fc06(addr):
        raise KeyError(addr)
    if addr == 0x4003 and not 1 <= value <= 247:
        raise ValueError("Modbus ID must be 1..247")
    if addr == 0x4004 and value not in (1200, 2400, 4800, 9600):
        raise ValueError("PRO2 baud must be 1200, 2400, 4800 or 9600")
    if addr == 0x400F and value not in (1, 4, 5, 6, 9, 10):
        raise ValueError("invalid PRO2 combination code")
    if addr == 0x4010 and not 1 <= value <= 30:
        raise ValueError("LCD cycle time must be 1..30")
    if addr == 0x4011 and value not in (1, 2, 3):
        raise ValueError("parity must be 1=even, 2=none or 3=odd")
    if addr == 0x6048 and value not in (1, 2, 11, 12):
        raise ValueError("invalid PRO2 tariff")
    with _lock:
        _config[addr] = int(value) & 0xFFFF


def write_fc10(addr: int, words: Tuple[int, int]) -> None:
    if not supported_fc10(addr, 2):
        raise KeyError(addr)
    import struct
    raw = struct.pack(">HH", words[0] & 0xFFFF, words[1] & 0xFFFF)
    value = struct.unpack(">f", raw)[0]
    if addr == 0x400D and value not in _S0_RATES:
        raise ValueError("invalid PRO2 S0 output rate")
    if addr == 0x6049 and value != 0.0:
        raise ValueError("PRO2 resettable day counter write is reset-to-zero")
    with _lock:
        _config[addr] = float(value)


def reset_day_counter() -> None:
    with _lock:
        _config[0x6049] = 0.0
