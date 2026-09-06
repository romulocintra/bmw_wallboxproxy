"""Deterministic electrical values for hardware diagnostics across all meter profiles."""

import threading

TEST_CURRENT_SEQUENCE_A = (0.0, 6.0, 10.0, 16.0, 20.0, 25.0, 32.0, 25.0, 20.0, 16.0, 10.0, 6.0)
_sequence_lock = threading.Lock()
_sequence_index = 0


def reset_test_sequence() -> None:
    global _sequence_index
    with _sequence_lock:
        _sequence_index = 0


def next_test_values() -> dict[str, float]:
    """Return a deterministic, internally coherent three-phase snapshot.

    Single-phase profiles (PRO2 and B21) collapse this snapshot to L1 in
    register_map.py. Three-phase profiles expose the same current on L1/L2/L3.
    """
    global _sequence_index
    with _sequence_lock:
        current = TEST_CURRENT_SEQUENCE_A[_sequence_index]
        _sequence_index = (_sequence_index + 1) % len(TEST_CURRENT_SEQUENCE_A)

    voltage = 230.0
    phase_power_kw = voltage * current / 1000.0
    total_power_kw = phase_power_kw * 3.0
    return {
        "voltage_avg": voltage,
        "u1": voltage, "u2": voltage, "u3": voltage,
        "freq": 50.0,
        "current_total": current * 3.0,
        "i1": current, "i2": current, "i3": current,
        "p_total": total_power_kw,
        "p1": phase_power_kw, "p2": phase_power_kw, "p3": phase_power_kw,
        "q_total": 0.0, "q1": 0.0, "q2": 0.0, "q3": 0.0,
        "s_total": total_power_kw,
        "s1": phase_power_kw, "s2": phase_power_kw, "s3": phase_power_kw,
        "pf_total": 1.0 if current else 0.0,
        "pf1": 1.0 if current else 0.0, "pf2": 1.0 if current else 0.0, "pf3": 1.0 if current else 0.0,
        "e_total": 100.0, "e_import": 100.0, "e_export": 0.0,
    }
