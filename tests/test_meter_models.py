import math
import struct

from bmw_wallboxproxy.meter_models import build_janitza_b23, build_inepro_pro380


def _u32(regs, addr):
    return (regs[addr] << 16) | regs[addr + 1]


def _s32(regs, addr):
    raw = _u32(regs, addr)
    return raw - (1 << 32) if raw & 0x80000000 else raw


def _f32(regs, addr):
    raw = struct.pack(">HH", regs[addr], regs[addr + 1])
    return struct.unpack(">f", raw)[0]


def test_janitza_b23_scaled_current_and_power():
    regs = build_janitza_b23({
        "u1": 230.1,
        "i1": 16.21,
        "p_total": -3728.5,
        "p1": -3728.5,
        "freq": 50.01,
    })

    assert _u32(regs, 0x5B00) == 2301
    assert _u32(regs, 0x5B0C) == 1621
    assert _s32(regs, 0x5B14) == -372850
    assert _u32(regs, 0x5B2C) == 5001


def test_janitza_b23_zeroes_unused_phases_for_single_phase_installation():
    regs = build_janitza_b23({"u1": 230.0, "i1": 10.0, "p_total": 2300.0})

    assert _u32(regs, 0x5B02) == 0
    assert _u32(regs, 0x5B0E) == 0
    assert _u32(regs, 0x5B10) == 0
    assert _u32(regs, 0x5B18) == 0
    assert _u32(regs, 0x5B1A) == 0


def test_inepro_pro380_keeps_float_encoding():
    regs = build_inepro_pro380({"p_total": 2.5, "i1": 10.0}, "abcd")
    assert math.isclose(_f32(regs, 0x5012), 2.5, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x500C), 10.0, rel_tol=1e-6)
