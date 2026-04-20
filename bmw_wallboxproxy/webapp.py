from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from config import (
    get_ha_auth_mode,
    get_ha_url,
    get_ha_verify_tls,
    is_supervisor_ha_mode,
)
from state import (
    ALLOWED_PHASE_ORDERS,
    get_float_word_order,
    get_compatibility_profile_name,
    get_phase_order,
    get_power_offset_watts,
    get_register_alias_mode,
    get_transport_mode,
    latest_values,
    modbus_log,
    net_log,
    set_phase_order,
    set_power_offset_watts,
    state_lock,
    stats,
    stats_lock,
    tcp_raw_log,
)
from register_map import get_output_values
import config

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)


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
    return render_template("dashboard.html", active_page="dashboard")


@app.route("/settings")
def settings():
    return redirect(url_for("index"))


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
    try:
        watts = float(data["watts"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "missing or invalid 'watts' field"}), 400
    set_power_offset_watts(watts)
    config.save_env_setting("POWER_OFFSET_WATTS", str(watts))
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
    reachability_code, reachability_label = _transport_reachability(st)
    st["transport_reachability_code"] = reachability_code
    st["transport_reachability"] = reachability_label
    return jsonify(
        {
            "values": values,
            "stats": st,
            "output": get_output_values(),
            "modbus_log": ml,
            "net_log": nl,
            "tcp_raw_log": tl,
        }
    )
