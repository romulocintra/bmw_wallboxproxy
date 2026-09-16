import struct

from meter_models import build_inepro_pro2
from pro2_state import reset_state


def _f32(regs, addr):
    raw = struct.pack(">HH", regs[addr], regs[addr + 1])
    return struct.unpack(">f", raw)[0]


def test_pro2_identity_defaults_match_reference_profile(monkeypatch):
    reset_state()
    monkeypatch.delenv("PRO2_SERIAL", raising=False)
    monkeypatch.delenv("PRO2_METER_CODE", raising=False)
    monkeypatch.delenv("PRO2_PROTOCOL_VERSION", raising=False)
    monkeypatch.delenv("PRO2_SOFTWARE_VERSION", raising=False)
    monkeypatch.delenv("PRO2_HARDWARE_VERSION", raising=False)

    regs = build_inepro_pro2({
        "u1": 230.0,
        "freq": 50.0,
        "i1": 6.0,
        "p_total": 1.32,
        "q_total": 0.0,
        "s_total": 1.38,
        "pf_total": 0.95,
        "e_import": 100.0,
        "e_export": 0.0,
    }, "abcd")

    assert _u32(regs, 0x4000) == 15060001
    assert regs[0x4002] == 0x0102
    assert _f32(regs, 0x4005) == pytest.approx(3.2)
    assert _f32(regs, 0x4007) == pytest.approx(1.18)
    assert _f32(regs, 0x4009) == pytest.approx(1.03)
    assert regs[0x400B] == 100
    assert regs[0x400C] == 5
    assert regs[0x401F] == 0
    assert regs[0x400F] == 1


def test_pro2_identity_can_match_a_physical_meter_capture(monkeypatch):
    reset_state()
    monkeypatch.setenv("PRO2_SERIAL", "15060001")
    monkeypatch.setenv("PRO2_METER_CODE", "0x0102")
    monkeypatch.setenv("PRO2_PROTOCOL_VERSION", "3.2")
    monkeypatch.setenv("PRO2_SOFTWARE_VERSION", "1.18")
    monkeypatch.setenv("PRO2_HARDWARE_VERSION", "1.03")
    monkeypatch.setenv("PRO2_METER_AMPS", "100")

    regs = build_inepro_pro2({"u1": 230.0, "freq": 50.0, "i1": 6.0}, "abcd")

    assert _u32(regs, 0x4000) == 15060001
    assert regs[0x4002] == 0x0102
    assert _f32(regs, 0x4005) == pytest.approx(3.2)
    assert _f32(regs, 0x4007) == pytest.approx(1.18)
    assert _f32(regs, 0x4009) == pytest.approx(1.03)
    assert regs[0x400B] == 100


def test_pro2_power_is_exposed_in_kw():
    reset_state()
    regs = build_inepro_pro2({"p_total": 3.5}, "abcd")
    assert abs(_f32(regs, 0x5012) - 3.5) < 1e-6


def test_pro2_l1_measurement_profile_includes_documented_zero_phase_registers():
    reset_state()
    regs = build_inepro_pro2({
        "u1": 230.0,
        "i1": 10.0,
        "p_total": 2.3,
        "freq": 50.0,
        "pf_total": 1.0,
    }, "abcd")
    assert abs(_f32(regs, 0x5002) - 230.0) < 1e-6
    assert abs(_f32(regs, 0x500C) - 10.0) < 1e-6
    assert abs(_f32(regs, 0x5012) - 2.3) < 1e-6
    assert _f32(regs, 0x5004) == 0.0
    assert _f32(regs, 0x500E) == 0.0
    assert _f32(regs, 0x5010) == 0.0


def _u32(regs, addr):
    return (regs[addr] << 16) | regs[addr + 1]


import pytest
