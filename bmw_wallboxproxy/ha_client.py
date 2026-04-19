import time
import requests
import urllib3

import config
from state import latest_values, state_lock, stats, stats_lock, stop_event, log_net

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def read_ha_state(entity_id: str):
    auth_token = config.get_ha_auth_token()
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    url = f"{config.get_ha_api_base_url()}/states/{entity_id}"
    try:
        r = requests.get(url, headers=headers, timeout=5, verify=config.get_ha_verify_tls())
        r.raise_for_status()
        raw = r.json().get("state", "0")
        with stats_lock:
            stats["ha_reads_ok"] += 1
        return float(raw)
    except Exception as e:
        with stats_lock:
            stats["ha_reads_fail"] += 1
        log_net(f"HA read error: {entity_id} -> {e}")
        return None


def ha_poller() -> None:
    log_net(
        "HA poller starting "
        f"url={config.get_ha_api_base_url()} "
        f"tls_verify={config.get_ha_verify_tls()} "
        f"auth_mode={config.get_ha_auth_mode()}"
    )

    if not config.has_ha_auth():
        log_net("HA startup error: no Home Assistant authentication is available")
        raise RuntimeError("No Home Assistant authentication is available.")

    while not stop_event.is_set():
        updates = {}
        for key, entity in config.get_ha_entities().items():
            value = read_ha_state(entity)
            if value is not None:
                updates[key] = value

        with state_lock:
            latest_values.update(updates)

        time.sleep(config.HA_POLL_SECONDS)