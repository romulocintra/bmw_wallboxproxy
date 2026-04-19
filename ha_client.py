import time
import requests
import urllib3

import config
from state import latest_values, state_lock, stats, stats_lock, stop_event, log_net

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def read_ha_state(entity_id: str):
    headers = {"Authorization": f"Bearer {config.HA_TOKEN}"}
    url = f"{config.get_ha_url()}/api/states/{entity_id}"
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
        f"HA poller starting url={config.get_ha_url()} tls_verify={config.get_ha_verify_tls()} token_present={'yes' if bool(config.HA_TOKEN) else 'no'}"
    )

    if not config.HA_TOKEN:
        log_net("HA startup error: HA_TOKEN environment variable is not set")
        raise RuntimeError("HA_TOKEN environment variable is not set.")

    while not stop_event.is_set():
        updates = {}
        for key, entity in config.get_ha_entities().items():
            value = read_ha_state(entity)
            if value is not None:
                updates[key] = value

        with state_lock:
            latest_values.update(updates)

        time.sleep(config.HA_POLL_SECONDS)