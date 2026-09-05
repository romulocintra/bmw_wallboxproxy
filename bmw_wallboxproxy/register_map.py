from typing import Dict

from config import get_meter_model
from modbus_codec import float_to_words
from meter_models import build_register_map as build_model_register_map
from state import get_float_word_order, get_phase_order, get_power_offset_override, get_register_alias_mode, latest_values, state_lock


def _apply_phase_order(order: str, a: float, b: float, c: float) -> tuple:
    idx = [int(x) - 1 for x in order.split(",")]
    src = (a, b, c)
    return src[idx[0]], src[idx[1]], src[idx[2]]


def _snapshot_output_values() -> dict:
    with state_lock:
        snap = latest_values.copy()

    def get(name: str, default: float = 0.0) -> float:
        return float(snap.get(name, default))

    order = get_phase_order()
    u1, u2, u3 = _apply_phase_order(order, get("u1"), get("u2"), get("u3"))
    i1, i2, i3 = _apply_phase_order(order, get("i1"), get("i2"), get("i3"))
    override = get_power_offset_override()
    offset_watts = override if override is not None else snap.get("power_offset", 0.0)
    offset_kw = offset_watts / 1000.0
    p_total = get("p_total") / 1000.0 + offset_kw
    raw_p1 = get("p1") / 1000.0 + offset_kw / 3.0
    raw_p2 = get("p2") / 1000.0 + offset_kw / 3.0
    raw_p3 = get("p3") / 1000.0 + offset_kw / 3.0
    p1, p2, p3 = _apply_phase_order(order, raw_p1, raw_p2, raw_p3)
    freq = get("freq")
    e_import = get("e_import_total")
    e_export = get("e_export_total")

    s_total = abs(p_total)
    s1, s2, s3 = abs(p1), abs(p2), abs(p3)

    return {
        "voltage_avg": (u1 + u2 + u3) / 3.0,
        "u1": u1, "u2": u2, "u3": u3,
        "freq": freq,
        "current_total": i1 + i2 + i3,
        "i1": i1, "i2": i2, "i3": i3,
        "p_total": p_total * 1000.0,
        "p1": p1 * 1000.0, "p2": p2 * 1000.0, "p3": p3 * 1000.0,
        "p_total_kw": p_total, "p1_kw": p1, "p2_kw": p2, "p3_kw": p3,
        "q_total": 0.0, "q1": 0.0, "q2": 0.0, "q3": 0.0,
        "s_total": s_total * 1000.0, "s1": s1 * 1000.0, "s2": s2 * 1000.0, "s3": s3 * 1000.0,
        "pf_total": p_total / s_total if s_total else 0.0,
        "pf1": p1 / s1 if s1 else 0.0,
        "pf2": p2 / s2 if s2 else 0.0,
        "pf3": p3 / s3 if s3 else 0.0,
        "e_total": e_import + e_export,
        "e_import": e_import,
        "e_export": e_export,
    }


def get_output_values() -> dict:
    return _snapshot_output_values()


def get_register_map() -> Dict[int, int]:
    values = _snapshot_output_values()
    model = get_meter_model()

    # Inepro maps expect active power in kW and the existing register builder
    # uses the legacy float layout. Janitza B23 expects signed/unsigned scaled
    # integer quantities in its 0x5Bxx map, so pass watts to that model.
    model_values = dict(values)
    if model in ("inepro_pro380", "inepro_pro2"):
        for key in ("p_total", "p1", "p2", "p3"):
            model_values[key] = values[key] / 1000.0
        for key in ("s_total", "s1", "s2", "s3"):
            model_values[key] = values[key] / 1000.0

    regs = build_model_register_map(model, model_values, get_float_word_order())

    # Preserve the existing alias compatibility option for the legacy Inepro
    # map. Janitza has fixed addresses and must not be shifted.
    if model in ("inepro_pro380", "inepro_pro2"):
        alias_mode = get_register_alias_mode()
        if alias_mode != "exact":
            aliased = dict(regs)
            for addr in list(regs):
                if addr + 1 not in regs:
                    continue
                words = (regs[addr], regs[addr + 1])
                if alias_mode in ("alias_minus_1", "alias_both"):
                    aliased[addr - 1] = words[0]
                    aliased[addr] = words[1]
                if alias_mode in ("alias_plus_1", "alias_both"):
                    aliased[addr + 1] = words[0]
                    aliased[addr + 2] = words[1]
            regs = aliased

    return regs
