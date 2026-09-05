import math
import struct

from bmw_wallboxproxy.meter_models import (
    build_janitza_b23,
    build_inepro_pro2,
    build_inepro_pro380,
    build_register_map,
)


def _u32(regs, addr):
    return (regs[addr] << 16) | regs[addr + 1]


def _s32(regs, addr):
    raw = _u32(regs, addr)
    return raw - (1 << 32) if raw & 0x80000000 else raw


def _f32(regs, addr):
    raw = struct.pack(">HH", regs[addr], regs[addr + 1])
    return struct.unpack(">f", raw)[0]


def test_inepro_pro380_documented_measurement_encoding():
    regs = build_inepro_pro380({
        "voltage_avg": 230.0,
        "u1": 230.1,
        "u2": 229.9,
        "u3": 230.2,
        "freq": 50.0,
        "current_total": 16.21,
        "i1": 16.21,
        "i2": 0.0,
        "i3": 0.0,
        "p_total": 3.7285,
        "p1": 3.7285,
        "q_total": 0.0,
        "s_total": 3.7285,
        "pf_total": 1.0,
    }, "abcd")

    assert math.isclose(_f32(regs, 0x5000), 230.0, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x500C), 16.21, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x5012), 3.7285, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x502A), 1.0, rel_tol=1e-6)


def test_inepro_pro380_energy_registers_match_documented_addresses():
    regs = build_inepro_pro380({
        "e_total": 1234.5,
        "e_import": 1000.25,
        "e_export": 234.25,
    }, "abcd")

    assert math.isclose(_f32(regs, 0x6000), 1234.5, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x600C), 1000.25, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x6018), 234.25, rel_tol=1e-6)

    # T1/T2 and phase-specific energy are not available from HA, so they must
    # not incorrectly duplicate aggregate counters.
    for addr in (0x6002, 0x6004, 0x6006, 0x6008, 0x600A,
                 0x600E, 0x6010, 0x6012, 0x6014, 0x6016,
                 0x601A, 0x601C, 0x601E, 0x6020, 0x6022,
                 0x6024, 0x6026, 0x6028, 0x602A, 0x602C, 0x602E,
                 0x6030, 0x6032, 0x6034, 0x6036, 0x6038, 0x603A,
                 0x603C, 0x603E, 0x6040, 0x6042, 0x6044, 0x6046):
        assert math.isclose(_f32(regs, addr), 0.0, abs_tol=1e-9)

    assert regs[0x6048] == 0
    assert math.isclose(_f32(regs, 0x6049), 0.0, abs_tol=1e-9)


def test_inepro_pro2_is_single_phase():
    regs = build_inepro_pro2({
        "voltage_avg": 230.0,
        "u1": 230.0,
        "freq": 50.0,
        "current_total": 16.21,
        "i1": 16.21,
        "p_total": 3.7285,
        "q_total": 0.0,
        "s_total": 3.7285,
        "pf_total": 1.0,
        "e_total": 123.4,
        "e_import": 120.0,
        "e_export": 3.4,
    }, "abcd")

    assert math.isclose(_f32(regs, 0x5002), 230.0, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x500C), 16.21, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x5012), 3.7285, rel_tol=1e-6)

    for addr in (0x5004, 0x5006, 0x500E, 0x5010,
                 0x5014, 0x5016, 0x5018,
                 0x501C, 0x501E, 0x5020,
                 0x5024, 0x5026, 0x5028,
                 0x502C, 0x502E, 0x5030):
        assert math.isclose(_f32(regs, addr), 0.0, abs_tol=1e-9)


def test_meter_model_dispatch_and_invalid_model():
    regs = build_register_map("inepro_pro2", {"i1": 5.0}, "abcd")
    assert math.isclose(_f32(regs, 0x500C), 5.0, rel_tol=1e-6)

    try:
        build_register_map("not-a-meter", {}, "abcd")
    except ValueError as exc:
        assert "Unsupported meter model" in str(exc)
    else:
        raise AssertionError("unsupported meter model must fail")


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
