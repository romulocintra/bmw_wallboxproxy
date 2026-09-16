"""Deterministic electrical values for hardware diagnostics across all meter profiles."""

import math
import threading

import config

TEST_CURRENT_SEQUENCE_A = (0.0, 6.0, 10.0, 16.0, 20.0, 25.0, 32.0, 25.0, 20.0, 16.0, 10.0, 6.0)
_sequence_lock = threading.Lock()
_sequence_index = 0


def reset_test_sequence() -> None:
    global _sequence_index
    with _sequence_lock:
        _sequence_index = 0


def next_test_values() -> dict[str, float]:
    """Return a deterministic, internally coherent three-phase snapshot.

    A configured TEST_CURRENT_A overrides the built-in current sequence. The
    other TEST_* settings provide custom voltage, frequency and power factor.
    Single-phase profiles (PRO2 and B21) collapse this snapshot to L1 in
    register_map.py. Three-phase profiles expose the same current on L1/L2/L3.
    """
    global _sequence_index
    if config.TEST_CURRENT_A is not None:
        current = config.TEST_CURRENT_A
    else:
        with _sequence_lock:
            current = TEST_CURRENT_SEQUENCE_A[_sequence_index]
            _sequence_index = (_sequence_index + 1) % len(TEST_CURRENT_SEQUENCE_A)

    voltage = config.TEST_VOLTAGE_V
    frequency = config.TEST_FREQUENCY_HZ
    power_factor = config.TEST_POWER_FACTOR
    apparent_power_kva = voltage * current / 1000.0
    phase_power_kw = apparent_power_kva * power_factor
    phase_reactive_kvar = apparent_power_kva * math.sqrt(max(0.0, 1.0 - power_factor * power_factor))
    total_power_kw = phase_power_kw * 3.0
    total_reactive_kvar = phase_reactive_kvar * 3.0
    total_apparent_kva = apparent_power_kva * 3.0
    return {
        "voltage_avg": voltage,
        "u1": voltage, "u2": voltage, "u3": voltage,
        "freq": frequency,
        "current_total": current * 3.0,
        "i1": current, "i2": current, "i3": current,
        "p_total": total_power_kw,
        "p1": phase_power_kw, "p2": phase_power_kw, "p3": phase_power_kw,
        "q_total": total_reactive_kvar,
        "q1": phase_reactive_kvar, "q2": phase_reactive_kvar, "q3": phase_reactive_kvar,
        "s_total": total_apparent_kva,
        "s1": apparent_power_kva, "s2": apparent_power_kva, "s3": apparent_power_kva,
        "pf_total": power_factor if current else 0.0,
        "pf1": power_factor if current else 0.0,
        "pf2": power_factor if current else 0.0,
        "pf3": power_factor if current else 0.0,
        "e_total": 100.0, "e_import": 100.0, "e_export": 0.0,
    }
