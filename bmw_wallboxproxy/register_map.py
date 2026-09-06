from typing import Dict

import config
from meter_models import build_register_map as build_model_register_map
from pro2_state import snapshot as pro2_snapshot
from state import (
    get_float_word_order,
    get_phase_order,
    get_power_offset_override,
    get_register_alias_mode,
    latest_values,
    state_lock,
)
from test_mode import next_test_values


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
    offset_kw = (override if override is not None else snap.get("power_offset", 0.0)) / 1000.0
    p_total = get("p_total") / 1000.0 + offset_kw
    raw_p1 = get("p1") / 1000.0 + offset_kw / 3.0
    raw_p2 = get("p2") / 1000.0 + offset_kw / 3.0
    raw_p3 = get("p3") / 1000.0 + offset_kw / 3.0
    p1, p2, p3 = _apply_phase_order(order, raw_p1, raw_p2, raw_p3)

    e_import = get("e_import_total")
    e_export = get("e_export_total")
    s_total = abs(p_total)
    s1, s2, s3 = abs(p1), abs(p2), abs(p3)

    return {
        "voltage_avg": (u1 + u2 + u3) / 3.0,
        "u1": u1, "u2": u2, "u3": u3,
        "freq": get("freq"),
        "current_total": i1 + i2 + i3,
        "i1": i1, "i2": i2, "i3": i3,
        "p_total": p_total, "p1": p1, "p2": p2, "p3": p3,
        "q_total": 0.0, "q1": 0.0, "q2": 0.0, "q3": 0.0,
        "s_total": s_total, "s1": s1, "s2": s2, "s3": s3,
        "pf_total": p_total / s_total if s_total else 0.0,
        "pf1": p1 / s1 if s1 else 0.0,
        "pf2": p2 / s2 if s2 else 0.0,
        "pf3": p3 / s3 if s3 else 0.0,
        "e_total": e_import + e_export,
        "e_import": e_import, "e_export": e_export,
    }


def get_output_values() -> dict:
    return _snapshot_output_values()


def _build_model_values(values: dict, model: str, test_mode: bool = False) -> dict:
    model_values = dict(values)

    if model in ("janitza_b21", "janitza_b23"):
        for key in ("p_total", "p1", "p2", "p3", "s_total", "s1", "s2", "s3"):
            model_values[key] = values[key] * 1000.0

    if model in ("inepro_pro2", "janitza_b21"):
        model_values["voltage_avg"] = values["u1"]
        model_values["u2"] = 0.0
        model_values["u3"] = 0.0
        model_values["current_total"] = values["i1"]
        model_values["i2"] = 0.0
        model_values["i3"] = 0.0
        if test_mode:
            model_values["p_total"] = model_values["p1"]
        model_values["p2"] = 0.0
        model_values["p3"] = 0.0
        model_values["q_total"] = 0.0
        model_values["q1"] = 0.0
        model_values["q2"] = 0.0
        model_values["q3"] = 0.0
        model_values["s_total"] = model_values["s1"]
        model_values["s1"] = abs(model_values["p1"])
        model_values["s2"] = 0.0
        model_values["s3"] = 0.0
        model_values["pf_total"] = model_values["pf1"]
        model_values["pf2"] = 0.0
        model_values["pf3"] = 0.0

    return model_values


def _apply_legacy_aliases(regs: Dict[int, int], alias_mode: str) -> Dict[int, int]:
    if alias_mode == "exact":
        return regs
    aliased = dict(regs)
    float_addresses = (
        0x5000, 0x5002, 0x5004, 0x5006, 0x5008, 0x500A, 0x500C, 0x500E,
        0x5010, 0x5012, 0x5014, 0x5016, 0x5018, 0x501A, 0x501C, 0x501E,
        0x5020, 0x5022, 0x5024, 0x5026, 0x5028, 0x502A, 0x502C, 0x502E,
        0x5030, 0x6000, 0x6002, 0x6004, 0x6006, 0x6008, 0x600A, 0x600C,
        0x600E, 0x6010, 0x6012, 0x6014, 0x6016, 0x6018, 0x601A, 0x601C,
        0x601E, 0x6020, 0x6022, 0x6024, 0x6026, 0x6028, 0x602A, 0x602C,
        0x602E, 0x6030, 0x6032, 0x6034, 0x6036, 0x6038, 0x603A, 0x603C,
        0x603E, 0x6040, 0x6042, 0x6044, 0x6046, 0x6049,
    )
    for addr in float_addresses:
        if addr not in regs or addr + 1 not in regs:
            continue
        hi, lo = regs[addr], regs[addr + 1]
        if alias_mode in ("alias_minus_1", "alias_both"):
            aliased[addr - 1] = hi
            aliased[addr] = lo
        if alias_mode in ("alias_plus_1", "alias_both"):
            aliased[addr + 1] = hi
            aliased[addr + 2] = lo
    return aliased


def _apply_pro2_runtime_config(regs: Dict[int, int]) -> Dict[int, int]:
    cfg = pro2_snapshot()
    for addr in (0x4003, 0x4004, 0x400F, 0x4010, 0x4011, 0x4016, 0x6048):
        regs[addr] = int(cfg[addr]) & 0xFFFF
    import struct
    for addr in (0x400D, 0x6049):
        raw = struct.pack(">f", float(cfg[addr]))
        regs[addr], regs[addr + 1] = struct.unpack(">HH", raw)
    return regs


def get_register_map() -> Dict[int, int]:
    # Import the module rather than binding get_meter_model by value. Tests and
    # runtime configuration can replace config.get_meter_model dynamically, and
    # the register map must observe that same model selection as dr_client.
    model = config.get_meter_model()
    test_mode = config.get_test_mode()
    values = next_test_values() if test_mode else _snapshot_output_values()
    regs = build_model_register_map(
        model,
        _build_model_values(values, model, test_mode=test_mode),
        get_float_word_order(),
    )
    if model == "inepro_pro2":
        regs = _apply_pro2_runtime_config(regs)
    if model in ("inepro_pro380", "inepro_pro2"):
        regs = _apply_legacy_aliases(regs, get_register_alias_mode())
    return regs
