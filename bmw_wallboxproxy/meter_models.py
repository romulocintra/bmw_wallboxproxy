from typing import Callable, Dict

from modbus_codec import float_to_words, to_float32_safe


RegisterEncoder = Callable[[float], tuple[int, ...]]


def _float_encoder(word_order: str) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]:
        return float_to_words(to_float32_safe(value), word_order)

    return encode


def _scaled_u32(scale: float) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]:
        raw = max(0, int(round(float(value) / scale)))
        raw = min(raw, 0xFFFFFFFF)
        return ((raw >> 16) & 0xFFFF, raw & 0xFFFF)

    return encode


def _scaled_s32(scale: float) -> RegisterEncoder:
    def encode(value: float) -> tuple[int, ...]:
        raw = int(round(float(value) / scale))
        raw = max(-0x80000000, min(raw, 0x7FFFFFFF))
        raw &= 0xFFFFFFFF
        return ((raw >> 16) & 0xFFFF, raw & 0xFFFF)

    return encode


def _put_float(regs: Dict[int, int], enc: RegisterEncoder, addr: int, value: float) -> None:
    hi, lo = enc(value)
    regs[addr] = hi
    regs[addr + 1] = lo


def _put_u16(regs: Dict[int, int], addr: int, value: int) -> None:
    regs[addr] = int(value) & 0xFFFF


def _value(values: dict, name: str, default: float = 0.0) -> float:
    return float(values.get(name, default))


def build_inepro_pro380(values: dict, word_order: str) -> Dict[int, int]:
    """Build the documented Inepro PRO380-Mod FLOAT32 register map."""
    enc = _float_encoder(word_order)
    regs: Dict[int, int] = {}

    measurement_values = {
        0x5000: _value(values, "voltage_avg"),
        0x5002: _value(values, "u1"),
        0x5004: _value(values, "u2"),
        0x5006: _value(values, "u3"),
        0x5008: _value(values, "freq"),
        0x500A: _value(values, "current_total"),
        0x500C: _value(values, "i1"),
        0x500E: _value(values, "i2"),
        0x5010: _value(values, "i3"),
        0x5012: _value(values, "p_total"),
        0x5014: _value(values, "p1"),
        0x5016: _value(values, "p2"),
        0x5018: _value(values, "p3"),
        0x501A: _value(values, "q_total"),
        0x501C: _value(values, "q1"),
        0x501E: _value(values, "q2"),
        0x5020: _value(values, "q3"),
        0x5022: _value(values, "s_total"),
        0x5024: _value(values, "s1"),
        0x5026: _value(values, "s2"),
        0x5028: _value(values, "s3"),
        0x502A: _value(values, "pf_total"),
        0x502C: _value(values, "pf1"),
        0x502E: _value(values, "pf2"),
        0x5030: _value(values, "pf3"),
    }
    for addr, value in measurement_values.items():
        _put_float(regs, enc, addr, value)

    energy_values = {
        0x6000: _value(values, "e_total"),
        0x6002: 0.0, 0x6004: 0.0,
        0x6006: 0.0, 0x6008: 0.0, 0x600A: 0.0,
        0x600C: _value(values, "e_import"),
        0x600E: 0.0, 0x6010: 0.0,
        0x6012: 0.0, 0x6014: 0.0, 0x6016: 0.0,
        0x6018: _value(values, "e_export"),
        0x601A: 0.0, 0x601C: 0.0,
        0x601E: 0.0, 0x6020: 0.0, 0x6022: 0.0,
        0x6024: 0.0, 0x6026: 0.0, 0x6028: 0.0,
        0x602A: 0.0, 0x602C: 0.0, 0x602E: 0.0,
        0x6030: 0.0, 0x6032: 0.0, 0x6034: 0.0,
        0x6036: 0.0, 0x6038: 0.0, 0x603A: 0.0,
        0x603C: 0.0, 0x603E: 0.0, 0x6040: 0.0,
        0x6042: 0.0, 0x6044: 0.0, 0x6046: 0.0,
    }
    for addr, value in energy_values.items():
        _put_float(regs, enc, addr, value)

    regs[0x6048] = 0
    _put_float(regs, enc, 0x6049, 0.0)
    return regs


def build_inepro_pro2(values: dict, word_order: str) -> Dict[int, int]:
    """Emulate an Inepro PRO2-Mod as a single-phase physical meter.

    The profile follows the official PRO2-Mod Modbus map: read-only identity
    and configuration registers use their documented native types, while live
    measurements and energy values use FLOAT32 ABCD. Only PRO2 fields are
    populated; PRO380-only L2/L3 fields are not treated as real measurements.

    Device-unique fields (serial/version/checksum/status) cannot be derived
    from Home Assistant, so they use stable zero placeholders until a real
    meter identity is supplied. All documented default configuration fields
    are represented using the manufacturer's default values.
    """
    enc = _float_encoder(word_order)
    regs: Dict[int, int] = {}

    # PRO2-Mod read-only identity/configuration map. Defaults documented by
    # Inepro: ID 1, 9600 baud, 100 A meter, S0 1000 imp/kWh, combination C01,
    # LCD cycle 10 s, even parity, forward current direction. Serial/version,
    # checksum and status are device-specific and therefore remain zero.
    _put_u16(regs, 0x4000, 0x0000)
    _put_u16(regs, 0x4001, 0x0000)
    _put_u16(regs, 0x4002, 0x0000)
    _put_u16(regs, 0x4003, 1)
    _put_u16(regs, 0x4004, 9600)
    _put_float(regs, enc, 0x4005, 0.0)
    _put_float(regs, enc, 0x4007, 0.0)
    _put_float(regs, enc, 0x4009, 0.0)
    _put_u16(regs, 0x400B, 100)
    _put_float(regs, enc, 0x400D, 1000.0)
    _put_u16(regs, 0x400F, 1)   # C01: forward only
    _put_u16(regs, 0x4010, 10)  # default LCD cycle
    _put_u16(regs, 0x4011, 1)   # 1 = even
    _put_u16(regs, 0x4012, ord("F"))
    _put_u16(regs, 0x4015, 0)   # no error
    _put_u16(regs, 0x4016, 0)   # power-down counter
    _put_u16(regs, 0x4017, 1)   # forward active quadrant
    _put_u16(regs, 0x401B, 0)
    _put_u16(regs, 0x401C, 0)
    _put_u16(regs, 0x401D, 0)
    _put_u16(regs, 0x401E, 0)

    measurement_values = {
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
    for addr, value in measurement_values.items():
        _put_float(regs, enc, addr, value)

    # These addresses exist in the common register layout but are explicitly
    # marked PRO380-only in the PRO2 manual. They are not used as PRO2 data.
    for addr in (
        0x5004, 0x5006, 0x500E, 0x5010,
        0x5014, 0x5016, 0x5018,
        0x501C, 0x501E, 0x5020,
        0x5024, 0x5026, 0x5028,
        0x502C, 0x502E, 0x5030,
    ):
        _put_float(regs, enc, addr, 0.0)

    # Complete PRO2 energy map. Aggregate counters are sourced from HA;
    # tariff/phase/reactive counters not available from HA are zero rather
    # than being incorrectly duplicated from an aggregate counter.
    energy_values = {
        0x6000: _value(values, "e_total"),
        0x6002: 0.0, 0x6004: 0.0,
        0x6006: 0.0, 0x6008: 0.0, 0x600A: 0.0,
        0x600C: _value(values, "e_import"),
        0x600E: 0.0, 0x6010: 0.0,
        0x6012: 0.0, 0x6014: 0.0, 0x6016: 0.0,
        0x6018: _value(values, "e_export"),
        0x601A: 0.0, 0x601C: 0.0,
        0x601E: 0.0, 0x6020: 0.0, 0x6022: 0.0,
        0x6024: 0.0, 0x6026: 0.0, 0x6028: 0.0,
        0x602A: 0.0, 0x602C: 0.0, 0x602E: 0.0,
        0x6030: 0.0, 0x6032: 0.0, 0x6034: 0.0,
        0x6036: 0.0, 0x6038: 0.0, 0x603A: 0.0,
        0x603C: 0.0, 0x603E: 0.0, 0x6040: 0.0,
        0x6042: 0.0, 0x6044: 0.0, 0x6046: 0.0,
    }
    for addr, value in energy_values.items():
        _put_float(regs, enc, addr, value)

    regs[0x6048] = 1  # default tariff T1
    _put_float(regs, enc, 0x6049, 0.0)
    return regs


def build_janitza_b23(values: dict) -> Dict[int, int]:
    """Janitza B23 live-value map from the documented 0x5Bxx layout."""
    def f(name: str, default: float = 0.0) -> float:
        return float(values.get(name, default))

    regs: Dict[int, int] = {}

    def put(addr: int, words: tuple[int, int]) -> None:
        regs[addr], regs[addr + 1] = words

    u32_01 = _scaled_u32(0.1)
    u32_001 = _scaled_u32(0.01)
    s32_001 = _scaled_s32(0.01)

    put(0x5B00, u32_01(f("u1")))
    put(0x5B02, u32_01(f("u2")))
    put(0x5B04, u32_01(f("u3")))
    put(0x5B06, u32_01(0.0))
    put(0x5B08, u32_01(0.0))
    put(0x5B0A, u32_01(0.0))
    put(0x5B0C, u32_001(f("i1")))
    put(0x5B0E, u32_001(f("i2")))
    put(0x5B10, u32_001(f("i3")))
    put(0x5B12, u32_001(0.0))
    put(0x5B14, s32_001(f("p_total")))
    put(0x5B16, s32_001(f("p1")))
    put(0x5B18, s32_001(f("p2")))
    put(0x5B1A, s32_001(f("p3")))
    put(0x5B1C, s32_001(f("q_total")))
    put(0x5B1E, s32_001(f("q1")))
    put(0x5B20, s32_001(f("q2")))
    put(0x5B22, s32_001(f("q3")))
    put(0x5B24, s32_001(f("s_total")))
    put(0x5B26, s32_001(f("s1")))
    put(0x5B28, s32_001(f("s2")))
    put(0x5B2A, s32_001(f("s3")))
    put(0x5B2C, u32_001(f("freq")))
    return regs


METER_BUILDERS = {
    "inepro_pro380": build_inepro_pro380,
    "inepro_pro2": build_inepro_pro2,
    "janitza_b23": build_janitza_b23,
}


def build_register_map(model: str, values: dict, word_order: str = "abcd") -> Dict[int, int]:
    try:
        builder = METER_BUILDERS[model]
    except KeyError as exc:
        raise ValueError(f"Unsupported meter model: {model}") from exc
    return builder(values, word_order) if model != "janitza_b23" else builder(values)
