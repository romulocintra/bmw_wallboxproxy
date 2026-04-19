from flask import Flask, jsonify, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from config import (
    get_ha_entity_fields,
    get_ha_entities,
    get_ha_auth_mode,
    get_ha_url,
    get_ha_verify_tls,
    is_supervisor_ha_mode,
    get_runtime_settings_store,
    save_env_setting,
    update_ha_live_data_settings,
)
from state import (
    ALLOWED_FLOAT_WORD_ORDERS,
    ALLOWED_REGISTER_ALIAS_MODES,
    ALLOWED_TRANSPORT_MODES,
    COMPATIBILITY_PROFILES,
    apply_compatibility_profile,
    get_float_word_order,
    get_compatibility_profile_name,
    get_register_alias_mode,
    get_transport_mode,
    latest_values,
    modbus_log,
    net_log,
    set_float_word_order,
    set_register_alias_mode,
    set_transport_mode,
    state_lock,
    stats,
    stats_lock,
    tcp_raw_log,
)
from state import log_net

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)


def _ingress_base_path() -> str:
    base_path = request.headers.get("X-Ingress-Path") or request.script_root or "/"
    if not base_path.startswith("/"):
        base_path = f"/{base_path}"
    if not base_path.endswith("/"):
        base_path = f"{base_path}/"
    return base_path


def _relative_path(path: str) -> str:
    return _ingress_base_path() + path.lstrip("/")


@app.context_processor
def inject_template_paths():
    return {
        "ingress_base_path": _ingress_base_path(),
        "dashboard_path": url_for("index"),
        "settings_path": url_for("settings"),
        "static_css_path": url_for("static", filename="app.css"),
        "static_js_path": url_for("static", filename="app.js"),
        "api_state_path": url_for("api_state"),
        "api_transport_mode_path": url_for("api_transport_mode"),
        "api_float_word_order_path": url_for("api_float_word_order"),
        "api_register_alias_mode_path": url_for("api_register_alias_mode"),
        "api_compatibility_profile_path": url_for("api_compatibility_profile"),
        "api_ha_live_data_path": url_for("api_ha_live_data"),
    }


def _persist_runtime_settings() -> None:
    save_env_setting("MODBUS_TRANSPORT_MODE", get_transport_mode())
    save_env_setting("MODBUS_FLOAT_WORD_ORDER", get_float_word_order())
    save_env_setting("MODBUS_REGISTER_ALIAS_MODE", get_register_alias_mode())


def _transport_reachability(st: dict) -> tuple[str, str]:
    if st["tx_frames"] > 0:
        return "valid_modbus_seen", "Valid Modbus seen"
    if st["bytes_rx"] > 0:
        return "payload_seen", "Payload seen"
    if st["tcp_connected"]:
        return "connected_no_payload", "Connected but no payload"
    if st["tcp_connects"] > 0:
        return "client_disconnected", "Client connected earlier, now disconnected"
    return "waiting_for_client", "Listening for TCP client"


@app.route("/")
def index():
    return render_template("dashboard.html", active_page="dashboard")


@app.route("/settings")
def settings():
    return render_template(
        "settings.html",
        active_page="settings",
        ha_auth_mode=get_ha_auth_mode(),
        ha_entity_fields=get_ha_entity_fields(),
        ha_url=get_ha_url(),
        ha_verify_tls=get_ha_verify_tls(),
        is_supervisor_ha_mode=is_supervisor_ha_mode(),
        settings_store_path=get_runtime_settings_store(),
    )


@app.route("/api/state")
def api_state():
    with state_lock:
        values = latest_values.copy()
    with stats_lock:
        st = stats.copy()
        ml = list(modbus_log)
        nl = list(net_log)
        tl = list(tcp_raw_log)
    reachability_code, reachability_label = _transport_reachability(st)
    st["transport_reachability_code"] = reachability_code
    st["transport_reachability"] = reachability_label
    return jsonify(
        {
            "values": values,
            "stats": st,
            "modbus_log": ml,
            "net_log": nl,
            "tcp_raw_log": tl,
            "settings": {
                "transport_mode": get_transport_mode(),
                "transport_mode_options": list(ALLOWED_TRANSPORT_MODES),
                "float_word_order": get_float_word_order(),
                "float_word_order_options": list(ALLOWED_FLOAT_WORD_ORDERS),
                "register_alias_mode": get_register_alias_mode(),
                "register_alias_mode_options": list(ALLOWED_REGISTER_ALIAS_MODES),
                "compatibility_profile": get_compatibility_profile_name(),
                "compatibility_profile_options": ["custom", *list(COMPATIBILITY_PROFILES.keys())],
                "ha_auth_mode": get_ha_auth_mode(),
                "ha_url": get_ha_url(),
                "ha_verify_tls": get_ha_verify_tls(),
                "is_supervisor_ha_mode": is_supervisor_ha_mode(),
                "ha_entities": get_ha_entities(),
            },
        }
    )


@app.route("/api/settings/transport-mode", methods=["POST"])
def api_transport_mode():
    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "")).strip().lower()

    if mode not in ALLOWED_TRANSPORT_MODES:
        return jsonify({"ok": False, "error": "invalid transport mode"}), 400

    changed = set_transport_mode(mode)
    _persist_runtime_settings()
    return jsonify({"ok": True, "changed": changed, "transport_mode": get_transport_mode()})


@app.route("/api/settings/float-word-order", methods=["POST"])
def api_float_word_order():
    payload = request.get_json(silent=True) or {}
    word_order = str(payload.get("word_order", "")).strip().lower()

    if word_order not in ALLOWED_FLOAT_WORD_ORDERS:
        return jsonify({"ok": False, "error": "invalid float word order"}), 400

    changed = set_float_word_order(word_order)
    _persist_runtime_settings()
    return jsonify({"ok": True, "changed": changed, "float_word_order": get_float_word_order()})


@app.route("/api/settings/register-alias-mode", methods=["POST"])
def api_register_alias_mode():
    payload = request.get_json(silent=True) or {}
    alias_mode = str(payload.get("alias_mode", "")).strip().lower()

    if alias_mode not in ALLOWED_REGISTER_ALIAS_MODES:
        return jsonify({"ok": False, "error": "invalid register alias mode"}), 400

    changed = set_register_alias_mode(alias_mode)
    _persist_runtime_settings()
    return jsonify({"ok": True, "changed": changed, "register_alias_mode": get_register_alias_mode()})


@app.route("/api/settings/compatibility-profile", methods=["POST"])
def api_compatibility_profile():
    payload = request.get_json(silent=True) or {}
    profile_name = str(payload.get("profile", "")).strip().lower()

    if profile_name == "custom":
        return jsonify({"ok": True, "changed": False, "compatibility_profile": get_compatibility_profile_name()})

    if profile_name not in COMPATIBILITY_PROFILES:
        return jsonify({"ok": False, "error": "invalid compatibility profile"}), 400

    changed = apply_compatibility_profile(profile_name)
    _persist_runtime_settings()
    return jsonify({"ok": True, "changed": changed, "compatibility_profile": get_compatibility_profile_name()})


@app.route("/api/settings/ha-live-data", methods=["POST"])
def api_ha_live_data():
    payload = request.get_json(silent=True) or {}
    ha_url = str(payload.get("ha_url", "")).strip()
    verify_tls = bool(payload.get("ha_verify_tls", True))
    entities = payload.get("entities")

    if not isinstance(entities, dict):
        return jsonify({"ok": False, "error": "invalid entities payload"}), 400

    try:
        changed = update_ha_live_data_settings(ha_url, verify_tls, entities)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except OSError as exc:
        log_net(f"Failed to persist HA settings to {get_runtime_settings_store()}: {exc}")
        return jsonify({"ok": False, "error": f"failed to persist settings: {exc}"}), 500

    saved_entities = sum(1 for entity_id in get_ha_entities().values() if entity_id)
    log_net(
        f"Persisted HA settings to {get_runtime_settings_store()} "
        f"auth_mode={get_ha_auth_mode()} entities={saved_entities}"
    )

    return jsonify(
        {
            "ok": True,
            "changed": changed,
            "ha_url": get_ha_url(),
            "ha_verify_tls": get_ha_verify_tls(),
            "ha_entities": get_ha_entities(),
            "settings_store_path": get_runtime_settings_store(),
            "saved_entity_count": saved_entities,
        }
    )