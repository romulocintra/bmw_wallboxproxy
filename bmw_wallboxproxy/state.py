import threading
import time
from collections import deque
from typing import Dict

from config import (
    DEFAULTS,
    MODBUS_FLOAT_WORD_ORDER,
    MODBUS_REGISTER_ALIAS_MODE,
    MODBUS_TRANSPORT_MODE,
    PHASE_ORDER,
    POWER_OFFSET_WATTS,
)

ALLOWED_TRANSPORT_MODES = ("rtu_over_tcp", "modbus_tcp")
ALLOWED_FLOAT_WORD_ORDERS = ("abcd", "cdab")
ALLOWED_REGISTER_ALIAS_MODES = ("exact", "alias_minus_1", "alias_plus_1", "alias_both")
ALLOWED_PHASE_ORDERS = ("1,2,3", "1,3,2", "2,1,3", "2,3,1", "3,1,2", "3,2,1")
COMPATIBILITY_PROFILES = {
    "pro380-default": {
        "transport_mode": "rtu_over_tcp",
        "float_word_order": "abcd",
        "register_alias_mode": "exact",
    },
    "pro380-offset-minus-1": {
        "transport_mode": "rtu_over_tcp",
        "float_word_order": "abcd",
        "register_alias_mode": "alias_minus_1",
    },
    "pro380-swapped-words": {
        "transport_mode": "rtu_over_tcp",
        "float_word_order": "cdab",
        "register_alias_mode": "exact",
    },
    "pro380-offset-and-swapped": {
        "transport_mode": "rtu_over_tcp",
        "float_word_order": "cdab",
        "register_alias_mode": "alias_minus_1",
    },
    "gateway-modbus-tcp": {
        "transport_mode": "modbus_tcp",
        "float_word_order": "abcd",
        "register_alias_mode": "exact",
    },
}

state_lock = threading.Lock()
latest_values: Dict[str, float] = DEFAULTS.copy()
transport_mode = MODBUS_TRANSPORT_MODE
transport_mode_generation = 0
float_word_order = MODBUS_FLOAT_WORD_ORDER
register_alias_mode = MODBUS_REGISTER_ALIAS_MODE
power_offset_watts: float = POWER_OFFSET_WATTS
phase_order: str = PHASE_ORDER if PHASE_ORDER in ALLOWED_PHASE_ORDERS else "1,2,3"

stats_lock = threading.Lock()
stats = {
    "ha_reads_ok": 0,
    "ha_reads_fail": 0,
    "tcp_connects": 0,
    "tcp_disconnects": 0,
    "tcp_accept_errors": 0,
    "rx_frames": 0,
    "tx_frames": 0,
    "crc_fail": 0,
    "wrong_slave": 0,
    "short_frames": 0,
    "unsupported_fc": 0,
    "illegal_quantity": 0,
    "bytes_rx": 0,
    "bytes_tx": 0,
    "last_rx": "-",
    "last_tx": "-",
    "last_connect": "-",
    "last_disconnect": "-",
    "tcp_connected": False,
    "last_fc": "-",
    "last_start_addr": "-",
    "last_quantity": "-",
    "last_exception": "-",
    "last_crc_expected": "-",
    "last_crc_received": "-",
    "last_buffer_len": 0,
    "transport_mode": MODBUS_TRANSPORT_MODE,
    "last_transaction_id": "-",
    "mode_change_count": 0,
    "float_word_order": MODBUS_FLOAT_WORD_ORDER,
    "register_alias_mode": MODBUS_REGISTER_ALIAS_MODE,
    "compat_change_count": 0,
    "compatibility_profile": "custom",
    "power_offset_watts": POWER_OFFSET_WATTS,
    "phase_order": PHASE_ORDER if PHASE_ORDER in ALLOWED_PHASE_ORDERS else "1,2,3",
}

modbus_log = deque(maxlen=300)
net_log = deque(maxlen=300)
tcp_raw_log = deque(maxlen=500)
stop_event = threading.Event()


def _ts() -> str:
    return time.strftime("%H:%M:%S")


def log_modbus(msg: str) -> None:
    with stats_lock:
        modbus_log.appendleft(f"{_ts()}  {msg}")


def log_net(msg: str) -> None:
    with stats_lock:
        net_log.appendleft(f"{_ts()}  {msg}")


def log_tcp_raw(msg: str) -> None:
    entry = f"{_ts()}  {msg}"
    with stats_lock:
        tcp_raw_log.appendleft(entry)


def get_transport_mode() -> str:
    with state_lock:
        return transport_mode


def get_transport_mode_generation() -> int:
    with state_lock:
        return transport_mode_generation


def set_transport_mode(mode: str) -> bool:
    global transport_mode, transport_mode_generation

    if mode not in ALLOWED_TRANSPORT_MODES:
        raise ValueError(f"Unsupported transport mode: {mode}")

    changed = False
    with state_lock:
        if transport_mode != mode:
            transport_mode = mode
            transport_mode_generation += 1
            changed = True

    with stats_lock:
        stats["transport_mode"] = mode
        if changed:
            stats["mode_change_count"] += 1
        stats["compatibility_profile"] = get_compatibility_profile_name()

    if changed:
        log_net(f"Transport mode changed to {mode}")
    return changed


def get_float_word_order() -> str:
    with state_lock:
        return float_word_order


def set_float_word_order(word_order: str) -> bool:
    global float_word_order

    if word_order not in ALLOWED_FLOAT_WORD_ORDERS:
        raise ValueError(f"Unsupported float word order: {word_order}")

    changed = False
    with state_lock:
        if float_word_order != word_order:
            float_word_order = word_order
            changed = True

    with stats_lock:
        stats["float_word_order"] = word_order
        if changed:
            stats["compat_change_count"] += 1
        stats["compatibility_profile"] = get_compatibility_profile_name()

    if changed:
        log_net(f"Float word order changed to {word_order}")
    return changed


def get_register_alias_mode() -> str:
    with state_lock:
        return register_alias_mode


def set_register_alias_mode(alias_mode: str) -> bool:
    global register_alias_mode

    if alias_mode not in ALLOWED_REGISTER_ALIAS_MODES:
        raise ValueError(f"Unsupported register alias mode: {alias_mode}")

    changed = False
    with state_lock:
        if register_alias_mode != alias_mode:
            register_alias_mode = alias_mode
            changed = True

    with stats_lock:
        stats["register_alias_mode"] = alias_mode
        if changed:
            stats["compat_change_count"] += 1
        stats["compatibility_profile"] = get_compatibility_profile_name()

    if changed:
        log_net(f"Register alias mode changed to {alias_mode}")
    return changed


def get_power_offset_watts() -> float:
    with state_lock:
        return power_offset_watts


def set_power_offset_watts(watts: float) -> None:
    global power_offset_watts
    with state_lock:
        power_offset_watts = float(watts)
    with stats_lock:
        stats["power_offset_watts"] = float(watts)
    log_net(f"Power offset set to {watts:+.0f} W")


def get_phase_order() -> str:
    with state_lock:
        return phase_order


def set_phase_order(order: str) -> bool:
    global phase_order
    if order not in ALLOWED_PHASE_ORDERS:
        raise ValueError(f"Unsupported phase order: {order}")
    changed = False
    with state_lock:
        if phase_order != order:
            phase_order = order
            changed = True
    with stats_lock:
        stats["phase_order"] = order
    if changed:
        log_net(f"Phase order changed to {order}")
    return changed


def get_compatibility_profile_name() -> str:
    with state_lock:
        current = {
            "transport_mode": transport_mode,
            "float_word_order": float_word_order,
            "register_alias_mode": register_alias_mode,
        }

    for name, profile in COMPATIBILITY_PROFILES.items():
        if profile == current:
            return name
    return "custom"


def apply_compatibility_profile(profile_name: str) -> bool:
    profile = COMPATIBILITY_PROFILES.get(profile_name)
    if profile is None:
        raise ValueError(f"Unsupported compatibility profile: {profile_name}")

    transport_changed = set_transport_mode(profile["transport_mode"])
    word_order_changed = set_float_word_order(profile["float_word_order"])
    alias_changed = set_register_alias_mode(profile["register_alias_mode"])
    changed = transport_changed or word_order_changed or alias_changed

    with stats_lock:
        stats["compatibility_profile"] = profile_name

    if changed:
        log_net(f"Compatibility profile applied: {profile_name}")
    return changed


with stats_lock:
    stats["compatibility_profile"] = get_compatibility_profile_name()