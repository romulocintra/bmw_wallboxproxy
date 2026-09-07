from typing import Callable, Dict

from modbus_codec import float_to_words, to_float32_safe
from pro2_state import get_identity

RegisterEncoder = Callable[[float], tuple[int, ...]]


def _float_encoder(word_order: str) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]:
        return float_to_words(to_float32_safe(value), word_order)
    return encode


def _scaled_u32(scale: float) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]:
        raw = min(max(0, int(round(float(value) / scale))), 0xFFFFFFFF)
        return ((raw >> 16) & 0xFFFF, raw & 0xFFFF)
    return encode


def _scaled_s32(scale: float) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]:
        raw = max(-0x80000000, min(int(round(float(value) / scale)), 0x7FFFFFFF)) & 0xFFFFFFFF
        return ((raw >> 16) & 0xFFFF, raw & 0xFFFF)
    return encode


def _scaled_u16(scale: float) -> int:
    return max(0, min(int(round(float(scale))), 0xFFFF))


def _put_float(regs: Dict[int, int], enc: RegisterEncoder, addr: int, value: float) -> None:
    hi, lo = enc(value)
    regs[addr], regs[addr + 1] = hi, lo


def _put_u16(regs: Dict[int, int], addr: int, value: int) -> None:
    regs[addr] = int(value) & 0xFFFF


def _value(values: dict, name: str, default: float = 0.0) -> float:
    return float(values.get(name, default))


def _inepro_energy_values(values: dict) -> dict[int, float]:
    """Build the non-starred PRO2 energy registers from forward/reverse data."""
    forward = _value(values, "e_import")
    reverse = _value(values, "e_export")
    combo = int(values.get("combination_code", 1))
    if combo == 1:
        total = forward
    elif combo == 4:
        total = reverse
    elif combo == 5:
        total = forward + reverse
    elif combo == 6:
        total = reverse - forward
    elif combo in (9, 10):
        total = forward - reverse
    else:
        total = forward
    return {
        0x6000: total,
        0x6002: _value(values, "e_t1_total"),
        0x6004: _value(values, "e_t2_total"),
        0x600C: forward,
        0x600E: _value(values, "e_t1_forward"),
        0x6010: _value(values, "e_t2_forward"),
        0x6018: reverse,
        0x601A: _value(values, "e_t1_reverse"),
        0x601C: _value(values, "e_t2_reverse"),
        0x6024: _value(values, "e_reactive_total"),
        0x6026: _value(values, "e_t1_reactive"),
        0x6028: _value(values, "e_t2_reactive"),
        0x6030: _value(values, "e_forward_reactive"),
        0x6032: _value(values, "e_t1_forward_reactive"),
        0x6034: _value(values, "e_t2_forward_reactive"),
        0x603C: _value(values, "e_reverse_reactive"),
        0x603E: _value(values, "e_t1_reverse_reactive"),
        0x6040: _value(values, "e_t2_reverse_reactive"),
    }


def _inepro_pro2_measurement_values(values: dict) -> dict[int, float]:
    return {
        0x5000: _value(values, "voltage_avg"),
        0x5002: _value(values, "u1"),
        0x5008: _value(values, "freq"),
        0x500A: _value(values, "current_total"),
        0x500C: _value(values, "i1"),
        0x5012: _value(values, "p_total"),
        0x501A: _value(values, "q_total"),
        0x5022: _value(values, "s_total"),
        0x502A: _value(values, "pf_total"),
    }


def build_inepro_pro380(values: dict, word_order: str) -> Dict[int, int]:
    enc = _float_encoder(word_order)
    regs: Dict[int, int] = {}
    fields = {
        0x5000: "voltage_avg", 0x5002: "u1", 0x5004: "u2", 0x5006: "u3",
        0x5008: "freq", 0x500A: "current_total", 0x500C: "i1", 0x500E: "i2",
        0x5010: "i3", 0x5012: "p_total", 0x5014: "p1", 0x5016: "p2",
        0x5018: "p3", 0x501A: "q_total", 0x501C: "q1", 0x501E: "q2",
        0x5020: "q3", 0x5022: "s_total", 0x5024: "s1", 0x5026: "s2",
        0x5028: "s3", 0x502A: "pf_total", 0x502C: "pf1", 0x502E: "pf2", 0x5030: "pf3",
    }
    for addr, name in fields.items():
        _put_float(regs, enc, addr, _value(values, name))
    for addr, value in {
        **_inepro_energy_values(values),
        0x6006: 0.0, 0x6008: 0.0, 0x600A: 0.0,
        0x6012: 0.0, 0x6014: 0.0, 0x6016: 0.0,
        0x601E: 0.0, 0x6020: 0.0, 0x6022: 0.0,
        0x602A: 0.0, 0x602C: 0.0, 0x602E: 0.0,
        0x6036: 0.0, 0x6038: 0.0, 0x603A: 0.0,
        0x6042: 0.0, 0x6044: 0.0, 0x6046: 0.0,
    }.items():
        _put_float(regs, enc, addr, value)
    regs[0x6048] = 0
    _put_float(regs, enc, 0x6049, 0.0)
    return regs


def build_inepro_pro2(values: dict, word_order: str) -> Dict[int, int]:
    """Build the documented non-PRO380 PRO2-Mod register map.

    The manual explicitly marks L2/L3, CT-ratio and phase-specific entries
    with '*' as PRO380-only. PRO2 therefore exposes only the registers listed
    here; unsupported addresses are rejected by the Modbus dispatcher.
    """
    enc = _float_encoder("abcd")
    regs: Dict[int, int] = {}
    identity = get_identity()

    serial = int(identity[0x4000])
    _put_u16(regs, 0x4000, (serial >> 16) & 0xFFFF)
    _put_u16(regs, 0x4001, serial & 0xFFFF)
    _put_u16(regs, 0x4002, int(identity[0x4002]))
    _put_u16(regs, 0x400B, int(identity[0x400B]))
    for addr in (0x4005, 0x4007, 0x4009):
        _put_float(regs, enc, addr, float(identity[addr]))

    combo = int(values.get("combination_code", 1))
    tariff = int(values.get("tariff", 1))
    current = _value(values, "p_total")
    direction = ord("R") if current < 0 else ord("F")

    for addr, value in (
        (0x4003, int(values.get("modbus_id", 1))),
        (0x4004, int(values.get("baud", 9600))),
        (0x400F, combo),
        (0x4010, int(values.get("lcd_cycle", 10))),
        (0x4011, int(values.get("parity", 1))),
        (0x4012, direction),
        (0x4015, 0),
        (0x4016, int(values.get("power_down_counter", 0))),
        # The manual defines the field but not the numeric quadrant encoding.
        # Preserve the documented/default forward quadrant until a real meter
        # capture supplies the vendor-specific mapping.
        (0x4017, 1),
        (0x401B, int(values.get("checksum", 0))),
        (0x401C, 0),
        (0x401D, int(values.get("active_status", 0))),
        (0x401E, 0),
        (0x6048, tariff),
    ):
        _put_u16(regs, addr, value)

    _put_float(regs, enc, 0x400D, _value(values, "s0_rate", 10000.0))

    for addr, value in _inepro_pro2_measurement_values(values).items():
        _put_float(regs, enc, addr, value)

    for addr, value in _inepro_energy_values(values).items():
        _put_float(regs, enc, addr, value)

    _put_float(regs, enc, 0x6049, _value(values, "e_day_counter"))
    return regs


def _build_janitza_b_series(values: dict, single_phase: bool) -> Dict[int, int]:
    regs = {}
    u32_01, u32_001, s32_001 = _scaled_u32(0.1), _scaled_u32(0.01), _scaled_s32(0.01)
    u1, u2, u3 = _value(values, "u1"), _value(values, "u2"), _value(values, "u3")
    i1, i2, i3 = _value(values, "i1"), _value(values, "i2"), _value(values, "i3")
    p1, p2, p3 = _value(values, "p1"), _value(values, "p2"), _value(values, "p3")
    if single_phase:
        u2 = u3 = i2 = i3 = p2 = p3 = 0.0
    for addr, val in ((0x5B00, u1), (0x5B02, u2), (0x5B04, u3), (0x5B06, 0.0), (0x5B08, 0.0), (0x5B0A, 0.0)):
        hi, lo = u32_01(val); regs[addr], regs[addr + 1] = hi, lo
    for addr, val in ((0x5B0C, i1), (0x5B0E, i2), (0x5B10, i3), (0x5B12, 0.0)):
        hi, lo = u32_001(val); regs[addr], regs[addr + 1] = hi, lo
    for addr, val in ((0x5B14, _value(values, "p_total")), (0x5B16, p1), (0x5B18, p2), (0x5B1A, p3), (0x5B1C, _value(values, "q_total")), (0x5B1E, 0.0), (0x5B20, 0.0), (0x5B22, 0.0), (0x5B24, _value(values, "s_total")), (0x5B26, abs(p1)), (0x5B28, abs(p2)), (0x5B2A, abs(p3))):
        hi, lo = s32_001(val); regs[addr], regs[addr + 1] = hi, lo
    regs[0x5B2C] = _scaled_u16(_value(values, "freq") / 0.01)
    regs[0x5B2D] = 0
    return regs


def build_janitza_b23(values: dict, word_order: str = "abcd") -> Dict[int, int]:
    return _build_janitza_b_series(values, False)


def build_janitza_b21(values: dict, word_order: str = "abcd") -> Dict[int, int]:
    return _build_janitza_b_series(values, True)


METER_BUILDERS = {
    "inepro_pro380": build_inepro_pro380,
    "inepro_pro2": build_inepro_pro2,
    "janitza_b23": build_janitza_b23,
    "janitza_b21": build_janitza_b21,
}


def build_register_map(model: str, values: dict, word_order: str = "abcd") -> Dict[int, int]:
    try:
        return METER_BUILDERS[model](values, word_order)
    except KeyError as exc:
        raise ValueError(f"Unsupported meter model: {model}") from exc
