import os
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import meter_models
import pro2_state


def test_pro2_reference_identity_defaults(monkeypatch):
    for name in (
        "PRO2_SERIAL", "PRO2_METER_CODE", "PRO2_PROTOCOL_VERSION",
        "PRO2_SOFTWARE_VERSION", "PRO2_HARDWARE_VERSION", "PRO2_METER_AMPS",
        "PRO2_CT_RATE", "PRO2_CT_MODE",
    ):
        monkeypatch.delenv(name, raising=False)

    identity = pro2_state.get_identity()
    assert identity[0x4000] == 15060001
    assert identity[0x4002] == 0x0102
    assert identity[0x4005] == 3.2
    assert identity[0x4007] == 1.18
    assert identity[0x4009] == 1.03
    assert identity[0x400B] == 100
    assert identity[0x400C] == 5
    assert identity[0x401F] == 0


def test_pro2_register_map_contains_single_phase_reference_registers(monkeypatch):
    for name in ("PRO2_SERIAL", "PRO2_METER_CODE"):
        monkeypatch.delenv(name, raising=False)

    values = {
        "u1": 230.0, "u2": 0.0, "u3": 0.0,
        "i1": 19.32, "i2": 0.0, "i3": 0.0,
        "voltage_avg": 230.0, "current_total": 19.32,
        "freq": 50.0, "p_total": 4.443, "p1": 4.443,
        "p2": 0.0, "p3": 0.0, "q_total": 0.0,
        "s_total": 4.443, "pf_total": 1.0,
        "combination_code": 3, "modbus_id": 1, "baud": 9600,
        "parity": 1, "lcd_cycle": 10, "tariff": 1,
        "s0_rate": 1000.0, "e_day_counter": 0.0,
    }
    regs = meter_models.build_inepro_pro2(values, "abcd")

    assert regs[0x4002] == 0x0102
    assert regs[0x400C] == 5
    assert regs[0x400F] == 3
    assert regs[0x4012] == 0x3146
    assert regs[0x4013] == 0x2020
    assert regs[0x4014] == 0x2020
    assert regs[0x4017] == 1
    assert regs[0x4018] == 1
    assert regs[0x4019] == 0
    assert regs[0x401A] == 0
    assert regs[0x500A] == regs[0x500C]
    assert regs[0x500B] == regs[0x500D]


def test_pro2_export_uses_reverse_direction_and_quadrant():
    values = {
        "u1": 230.0, "u2": 0.0, "u3": 0.0,
        "i1": 8.0, "i2": 0.0, "i3": 0.0,
        "voltage_avg": 230.0, "current_total": 8.0,
        "freq": 50.0, "p_total": -1.84, "p1": -1.84,
        "p2": 0.0, "p3": 0.0, "q_total": 0.0,
        "s_total": 1.84, "pf_total": -1.0,
        "combination_code": 3, "modbus_id": 1, "baud": 9600,
        "parity": 1, "lcd_cycle": 10, "tariff": 1,
        "s0_rate": 1000.0, "e_day_counter": 0.0,
    }
    regs = meter_models.build_inepro_pro2(values, "abcd")

    assert regs[0x4012] == 0x3152
    assert regs[0x4017] == 4
    assert regs[0x4018] == 4
    assert regs[0x4019] == 0
    assert regs[0x401A] == 0
