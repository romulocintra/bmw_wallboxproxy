import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "bmw_wallboxproxy"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import config
import register_map
import state


def test_register_map_dispatches_to_janitza_and_preserves_output_units(monkeypatch):
    monkeypatch.setattr(config, "METER_MODEL", "janitza_b23")
    monkeypatch.setattr(state, "latest_values", {
        "u1": 230.0,
        "u2": 230.0,
        "u3": 230.0,
        "i1": 16.21,
        "i2": 0.0,
        "i3": 0.0,
        "p_total": 3728.5,
        "p1": 3728.5,
        "p2": 0.0,
        "p3": 0.0,
        "freq": 50.0,
        "e_import_total": 0.0,
        "e_export_total": 0.0,
        "power_offset": 0.0,
    })

    values = register_map.get_output_values()
    regs = register_map.get_register_map()

    # Existing consumers still see active power in kW.
    assert values["p_total"] == 3.7285
    # Janitza B23 receives the same value in its documented 0.01 W format.
    assert (regs[0x5B0C] << 16 | regs[0x5B0D]) == 1621
    assert (regs[0x5B14] << 16 | regs[0x5B15]) == 372850
    assert (regs[0x5B16] << 16 | regs[0x5B17]) == 372850
