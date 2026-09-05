import math
import struct
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import config
import register_map


def _f32(regs, addr):
    return struct.unpack(">f", struct.pack(">HH", regs[addr], regs[addr + 1]))[0]


def _set_values(monkeypatch, model):
    monkeypatch.setattr(config, "METER_MODEL", model)
    monkeypatch.setattr(register_map, "get_float_word_order", lambda: "abcd")
    monkeypatch.setattr(register_map, "get_register_alias_mode", lambda: "exact")
    monkeypatch.setattr(register_map, "get_power_offset_override", lambda: None)
    monkeypatch.setattr(register_map, "latest_values", {
        "u1": 230.0,
        "u2": 231.0,
        "u3": 232.0,
        "i1": 16.21,
        "i2": 2.0,
        "i3": 3.0,
        "p_total": 3728.5,
        "p1": 3200.0,
        "p2": 300.0,
        "p3": 228.5,
        "freq": 50.0,
        "e_import_total": 100.0,
        "e_export_total": 2.0,
        "power_offset": 0.0,
    })


def test_register_map_dispatches_to_janitza_and_preserves_output_units(monkeypatch):
    _set_values(monkeypatch, "janitza_b23")

    values = register_map.get_output_values()
    regs = register_map.get_register_map()

    assert math.isclose(values["p_total"], 3.7285)
    assert (regs[0x5B0C] << 16 | regs[0x5B0D]) == 1621
    assert (regs[0x5B14] << 16 | regs[0x5B15]) == 372850
    assert (regs[0x5B16] << 16 | regs[0x5B17]) == 320000


def test_register_map_preserves_pro380_float_units_and_power_offset(monkeypatch):
    _set_values(monkeypatch, "inepro_pro380")
    monkeypatch.setattr(register_map, "get_power_offset_override", lambda: 100.0)

    values = register_map.get_output_values()
    regs = register_map.get_register_map()

    assert math.isclose(values["p_total"], 3.8285)
    assert math.isclose(_f32(regs, 0x5012), 3.8285, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x5014), 3.233333333333333, rel_tol=1e-6)


def test_register_map_pro2_forces_single_phase(monkeypatch):
    _set_values(monkeypatch, "inepro_pro2")

    regs = register_map.get_register_map()

    assert math.isclose(_f32(regs, 0x5000), 230.0, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x500A), 16.21, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x500C), 16.21, rel_tol=1e-6)
    assert math.isclose(_f32(regs, 0x5012), 3.7285, rel_tol=1e-6)

    for addr in (0x5004, 0x5006, 0x500E, 0x5010, 0x5016, 0x5018):
        assert math.isclose(_f32(regs, addr), 0.0, abs_tol=1e-9)


def test_legacy_alias_mode_is_not_applied_to_janitza(monkeypatch):
    _set_values(monkeypatch, "janitza_b23")
    monkeypatch.setattr(register_map, "get_register_alias_mode", lambda: "alias_both")

    regs = register_map.get_register_map()
    assert 0x5B0B not in regs
    assert 0x5B0D in regs
