import math
import struct

import register_map
from test_mode import TEST_CURRENT_SEQUENCE_A, next_test_values, reset_test_sequence


def _f32(regs, address):
    return struct.unpack(">f", struct.pack(">HH", regs[address], regs[address + 1]))[0]


def test_test_mode_sequence_is_deterministic_and_wraps():
    reset_test_sequence()
    values=[next_test_values()["i1"] for _ in range(len(TEST_CURRENT_SEQUENCE_A))]
    assert values == list(TEST_CURRENT_SEQUENCE_A)
    assert next_test_values()["i1"] == TEST_CURRENT_SEQUENCE_A[0]


def test_test_mode_is_three_phase_coherent_source_data():
    reset_test_sequence(); values=next_test_values()
    assert values["u1"] == values["u2"] == values["u3"] == 230.0
    assert values["i1"] == values["i2"] == values["i3"] == 0.0
    assert values["p_total"] == 0.0
    values=next_test_values()
    assert values["i1"] == 6.0
    assert math.isclose(values["p_total"], 4.14, rel_tol=1e-6)
    assert math.isclose(values["p1"], 1.38, rel_tol=1e-6)


def test_test_mode_applies_to_all_meter_models(monkeypatch):
    monkeypatch.setattr(register_map, "get_test_mode", lambda: True)
    reset_test_sequence()
    for model in ("inepro_pro380", "inepro_pro2", "janitza_b23", "janitza_b21"):
        monkeypatch.setattr(register_map, "get_meter_model", lambda model=model: model)
        reset_test_sequence()
        regs=register_map.get_register_map()
        if model == "inepro_pro2":
            assert _f32(regs,0x500C) == 0.0
            assert _f32(regs,0x5002) == 230.0
        elif model == "janitza_b21":
            assert (regs[0x5B0C] << 16 | regs[0x5B0D]) == 0
            assert (regs[0x5B00] << 16 | regs[0x5B01]) == 2300
        elif model == "janitza_b23":
            assert (regs[0x5B0C] << 16 | regs[0x5B0D]) == 0
            assert (regs[0x5B00] << 16 | regs[0x5B01]) == 2300
        else:
            assert _f32(regs,0x500C) == 0.0


def test_single_phase_test_profiles_expose_only_l1(monkeypatch):
    monkeypatch.setattr(register_map, "get_test_mode", lambda: True)
    for model in ("inepro_pro2", "janitza_b21"):
        monkeypatch.setattr(register_map, "get_meter_model", lambda model=model: model)
        reset_test_sequence(); regs=register_map.get_register_map()
        if model == "inepro_pro2":
            assert _f32(regs,0x5004) == 0.0
            assert _f32(regs,0x5006) == 0.0
        else:
            assert (regs[0x5B02] << 16 | regs[0x5B03]) == 0
            assert (regs[0x5B04] << 16 | regs[0x5B05]) == 0


def test_single_phase_test_profiles_use_l1_power_as_total(monkeypatch):
    monkeypatch.setattr(register_map, "get_test_mode", lambda: True)
    for model in ("inepro_pro2", "janitza_b21"):
        monkeypatch.setattr(register_map, "get_meter_model", lambda model=model: model)
        reset_test_sequence()
        register_map.get_register_map()  # 0 A vector
        regs=register_map.get_register_map()  # 6 A vector
        if model == "inepro_pro2":
            assert math.isclose(_f32(regs,0x5012), 1.38, rel_tol=1e-6)
            assert math.isclose(_f32(regs,0x5022), 1.38, rel_tol=1e-6)
            assert math.isclose(_f32(regs,0x502A), 1.0, rel_tol=1e-6)
        else:
            assert (regs[0x5B14] << 16 | regs[0x5B15]) == 138000
            assert (regs[0x5B24] << 16 | regs[0x5B25]) == 138000
            assert (regs[0x5B3A] if 0x5B3A in regs else 0) == 0
