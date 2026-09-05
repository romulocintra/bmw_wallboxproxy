"""Deterministic electrical values used by the optional PRO2 test mode."""

import threading


# Values are deliberately spread around common single-phase charging limits so
# the Wallbox can be observed while the virtual meter moves through several
# load levels. One register poll advances one step.
TEST_CURRENT_SEQUENCE_A = (
    0.0,
    6.0,
    10.0,
    16.0,
    20.0,
    25.0,
    32.0,
    25.0,
    20.0,
    16.0,
    10.0,
    6.0,
)

_sequence_lock = threading.Lock()
_sequence_index = 0


def reset_test_sequence() -> None:
    global _sequence_index
    with _sequence_lock:
        _sequence_index = 0


def next_test_values() -> dict[str, float]:
    """Return the next coherent single-phase PRO2 measurement snapshot."""
    global _sequence_index
    with _sequence_lock:
        current = TEST_CURRENT_SEQUENCE_A[_sequence_index]
        _sequence_index = (_sequence_index + 1) % len(TEST_CURRENT_SEQUENCE_A)

    voltage = 230.0
    power_w = voltage * current
    return {
        "voltage_avg": voltage,
        "u1": voltage,
        "u2": 0.0,
        "u3": 0.0,
        "freq": 50.0,
        "current_total": current,
        "i1": current,
        "i2": 0.0,
        "i3": 0.0,
        "p_total": power_w / 1000.0,
        "p1": power_w / 1000.0,
        "p2": 0.0,
        "p3": 0.0,
        "q_total": 0.0,
        "q1": 0.0,
        "q2": 0.0,
        "q3": 0.0,
        "s_total": power_w / 1000.0,
        "s1": power_w / 1000.0,
        "s2": 0.0,
        "s3": 0.0,
        "pf_total": 1.0 if current else 0.0,
        "pf1": 1.0 if current else 0.0,
        "pf2": 0.0,
        "pf3": 0.0,
        "e_total": 100.0,
        "e_import": 100.0,
        "e_export": 0.0,
    }
