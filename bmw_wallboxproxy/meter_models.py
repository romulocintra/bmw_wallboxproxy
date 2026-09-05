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


def build_inepro_pro380(values: dict, word_order: str) -> Dict[int, int]:
    """Inepro PRO380/PRO2-compatible FLOAT32 ABCD-style map."""
    def f(name: str, default: float = 0.0) -> float:
        return float(values.get(name, default))

    enc = _float_encoder(word_order)
    specs = {
        0x5000: f("voltage_avg"), 0x5002: f("u1"), 0x5004: f("u2"), 0x5006: f("u3"),
        0x5008: f("freq"), 0x500A: f("current_total"),
        0x500C: f("i1"), 0x500E: f("i2"), 0x5010: f("i3"),
        0x5012: f("p_total"), 0x5014: f("p1"), 0x5016: f("p2"), 0x5018: f("p3"),
        0x501A: f("q_total"), 0x501C: f("q1"), 0x501E: f("q2"), 0x5020: f("q3"),
        0x5022: f("s_total"), 0x5024: f("s1"), 0x5026: f("s2"), 0x5028: f("s3"),
        0x502A: f("pf_total"), 0x502C: f("pf1"), 0x502E: f("pf2"), 0x5030: f("pf3"),
        0x6000: f("e_total"), 0x6002: 0.0, 0x6004: 0.0,
        0x6006: 0.0, 0x6008: 0.0, 0x600A: 0.0,
        0x600C: f("e_import"), 0x600E: 0.0, 0x6010: 0.0,
        0x6012: 0.0, 0x6014: 0.0, 0x6016: 0.0,
        0x6018: f("e_export"), 0x601A: 0.0, 0x601C: 0.0,
        0x601E: 0.0, 0x6020: 0.0, 0x6022: 0.0,
    }
    regs: Dict[int, int] = {}
    for addr, value in specs.items():
        hi, lo = enc(value)
        regs[addr] = hi
        regs[addr + 1] = lo
    return regs


def build_janitza_b23(values: dict) -> Dict[int, int]:
    """Janitza B23 live-value map from the official Modbus register layout.

    B23 values use two 16-bit registers per measurement. Integer values are
    scaled engineering values, big-endian within the 32-bit quantity.
    """
    def f(name: str, default: float = 0.0) -> float:
        return float(values.get(name, default))

    regs: Dict[int, int] = {}

    def put(addr: int, words: tuple[int, int]) -> None:
        regs[addr], regs[addr + 1] = words

    u32_01 = _scaled_u32(0.1)
    u32_001 = _scaled_u32(0.01)
    s32_001 = _scaled_s32(0.01)

    # Voltage: 0.1 V; current: 0.01 A; frequency: 0.01 Hz.
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

    # Active/reactive/apparent power: 0.01 W/var/VA, signed.
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
    "inepro_pro2": build_inepro_pro380,
    "janitza_b23": build_janitza_b23,
}


def build_register_map(model: str, values: dict, word_order: str = "abcd") -> Dict[int, int]:
    try:
        builder = METER_BUILDERS[model]
    except KeyError as exc:
        raise ValueError(f"Unsupported meter model: {model}") from exc
    return builder(values, word_order) if model != "janitza_b23" else builder(values)
