import struct

import register_map
from test_mode import TEST_CURRENT_SEQUENCE_A, next_test_values, reset_test_sequence


def _float_from_registers(regs, address):
    raw = struct.pack(">HH", regs[address], regs[address + 1])
    return struct.unpack(">f", raw)[0]


def test_test_mode_sequence_is_deterministic_and_wraps():
    reset_test_sequence()
    values = [next_test_values()["i1"] for _ in range(len(TEST_CURRENT_SEQUENCE_A))]
    assert values == list(TEST_CURRENT_SEQUENCE_A)
    assert next_test_values()["i1"] == TEST_CURRENT_SEQUENCE_A[0]


def test_test_mode_builds_coherent_single_phase_values(monkeypatch):
    reset_test_sequence()
    values = next_test_values()
    assert values["u1"] == 230.0
    assert values["u2"] == 0.0
    assert values["u3"] == 0.0
    assert values["i1"] == 0.0
    assert values["p_total"] == 0.0
    assert values["pf_total"] == 0.0

    values = next_test_values()
    assert values["i1"] == 6.0
    assert values["p_total"] == 1.38
    assert values["p1"] == 1.38


def test_pro2_test_mode_changes_modbus_current_without_home_assistant(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setattr(register_map, "get_meter_model", lambda: "inepro_pro2")
    reset_test_sequence()

    first = register_map.get_register_map()
    second = register_map.get_register_map()

    assert _float_from_registers(first, 0x500C) == 0.0
    assert _float_from_registers(second, 0x500C) == 6.0
    assert _float_from_registers(second, 0x5002) == 230.0
    assert _float_from_registers(second, 0x5012) == 1.38


def test_test_mode_is_ignored_for_other_meter_models(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setattr(register_map, "get_meter_model", lambda: "inepro_pro380")
    reset_test_sequence()

    regs = register_map.get_register_map()
    assert _float_from_registers(regs, 0x500C) == 0.0
