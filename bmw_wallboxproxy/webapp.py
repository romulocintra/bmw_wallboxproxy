from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from config import (
    get_ha_auth_mode,
    get_ha_entities,
    get_ha_entity_fields,
    get_ha_url,
    get_ha_verify_tls,
    get_meter_model,
    is_supervisor_ha_mode,
)
from state import (
    ALLOWED_PHASE_ORDERS,
    get_ha_data_age_seconds,
    get_float_word_order,
    get_compatibility_profile_name,
    get_phase_order,
    get_power_offset_override,
    get_register_alias_mode,
    get_transport_mode,
    latest_values,
    modbus_log,
    net_log,
    set_phase_order,
    set_power_offset_override,
    state_lock,
    stats,
    stats_lock,
    tcp_raw_log,
)
from register_map import get_output_values
import config

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

METER_PROFILES = {
    "inepro_pro380": {
        "label": "Inepro PRO380",
        "phases": "3-phase",
        "encoding": "IEEE-754 FLOAT32",
        "byte_order": "ABCD by default",
        "serial": "9600 8E1, Modbus ID 1",
        "current_register": "0x500C",
        "required": ["u1", "u2", "u3", "i1", "i2", "i3", "p_total", "freq"],
        "recommended": ["p1", "p2", "p3", "e_import_total", "e_export_total"],
        "optional": ["power_offset"],
        "notes": "Use when the BMW Installation App is configured for Inepro PRO380. L2/L3 are real three-phase outputs.",
    },
    "inepro_pro2": {
        "label": "Inepro PRO2-Mod",
        "phases": "1-phase",
        "encoding": "IEEE-754 FLOAT32",
        "byte_order": "ABCD by default",
        "serial": "9600 8E1, Modbus ID 1",
        "current_register": "0x500C",
        "required": ["i1"],
        "recommended": ["u1", "p_total", "freq", "p1"],
        "optional": ["e_import_total", "e_export_total", "power_offset"],
        "notes": "Use for a single-phase installation when the BMW Installation App is configured for Inepro PRO2. L2/L3 inputs are not required and are ignored by the PRO2 model.",
    },
    "janitza_b23": {
        "label": "Janitza B23 312-10J",
        "phases": "3-phase",
        "encoding": "32-bit scaled integers",
        "byte_order": "Register-specific B23 representation",
        "serial": "Must match the BMW Installation App",
        "current_register": "0x5B0C",
        "required": ["u1", "u2", "u3", "i1", "i2", "i3", "p_total", "freq"],
        "recommended": ["p1", "p2", "p3", "e_import_total", "e_export_total"],
        "optional": ["power_offset"],
        "notes": "Use when the BMW Installation App is configured for Janitza B23. Do not apply Inepro FLOAT32 assumptions to this profile.",
    },
}


def _profile_view(model: str) -> dict:
    profile = METER_PROFILES.get(model, METER_PROFILES["inepro_pro380"])
    entities = get_ha_entities()
    required = set(profile["required"])
    recommended = set(profile["recommended"])
    optional = set(profile["optional"])
    fields = []
    for key, label, help_text in config.ENTITY_FIELDS:
        if key in required:
            role = "required"
        elif key in recommended:
            role = "recommended"
        elif key in optional:
            role = "optional"
        else:
            role = "not_used"
        fields.append({
            "key": key,
            "label": label,
            "help": help_text,
            "value": entities.get(key, ""),
            "role": role,
            "used": role != "not_used",
        })
    return {
        "key": model,
        **profile,
        "fields": fields,
    }


def _ingress_base_path() -> str:
    base_path = request.headers.get("X-Ingress-Path") or request.script_root or "/"
    if not base_path.startswith("/"):
        base_path = f"/{base_path}"
    if not base_path.endswith("/"):
        base_path = f"{base_path}/"
    return base_path


def _static_asset_text(filename: str) -> str:
    asset_path = Path(app.static_folder) / filename
    if not asset_path.exists():
        return ""
    return asset_path.read_text(encoding="utf-8")


@app.before_request
def apply_ingress_script_name() -> None:
    ingress_path = request.headers.get("X-Ingress-Path")
    if ingress_path:
        request.environ["SCRIPT_NAME"] = ingress_path.rstrip("/")


@app.context_processor
def inject_template_paths():
    return {
        "ingress_base_path": _ingress_base_path(),
        "api_state_path": url_for("api_state"),
        "inline_css": _static_asset_text("app.css"),
        "inline_js": _static_asset_text("app.js"),
    }


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
    model = get_meter_model()
    return render_template(
        "dashboard.html",
        active_page="dashboard",
        meter_model=model,
        meter_profile=_profile_view(model),
    )


@app.route("/settings")
def settings():
    model = get_meter_model()
    profile = _profile_view(model)
    return render_template(
        "settings.html",
        active_page="settings",
        ha_auth_mode=get_ha_auth_mode(),
        ha_url=get_ha_url(),
        ha_verify_tls=get_ha_verify_tls(),
        ha_entity_fields=get_ha_entity_fields(),
        meter_model=model,
        meter_profile=profile,
        meter_profiles=[_profile_view(key) for key in METER_PROFILES],
        supervisor_mode=is_supervisor_ha_mode(),
    )


@app.route("/api/phase_order", methods=["POST"])
def api_set_phase_order():
    data = request.get_json(force=True, silent=True) or {}
    order = str(data.get("order", "")).strip()
    if order not in ALLOWED_PHASE_ORDERS:
        return jsonify({"error": f"invalid phase order, must be one of: {', '.join(ALLOWED_PHASE_ORDERS)}"}), 400
    set_phase_order(order)
    config.save_env_setting("PHASE_ORDER", order)
    return jsonify({"order": order})


@app.route("/api/power_offset", methods=["POST"])
def api_set_power_offset():
    data = request.get_json(force=True, silent=True) or {}
    if "watts" in data and data["watts"] is None:
        set_power_offset_override(None)
        return jsonify({"watts": None})
    try:
        watts = float(data["watts"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "missing or invalid 'watts' field, send null to clear override"}), 400
    set_power_offset_override(watts)
    return jsonify({"watts": watts})


@app.route("/api/state")
def api_state():
    with state_lock:
        values = latest_values.copy()
    with stats_lock:
        st = stats.copy()
        ml = list(modbus_log)
        nl = list(net_log)
        tl = list(tcp_raw_log)
    age = get_ha_data_age_seconds()
    st["ha_data_age_seconds"] = None if age is None else round(age, 1)
    reachability_code, reachability_label = _transport_reachability(st)
    st["transport_reachability_code"] = reachability_code
    st["transport_reachability"] = reachability_label
    model = get_meter_model()
    return jsonify(
        {
            "values": values,
            "stats": st,
            "output": get_output_values(),
            "meter_model": model,
            "meter_profile": _profile_view(model),
            "modbus_log": ml,
            "net_log": nl,
            "tcp_raw_log": tl,
        }
    )
