import atexit
import logging
import threading
import sys
import os
import socket
import ssl
import signal
from pathlib import Path

from config import (
    MODBUS_LISTEN_HOST,
    MODBUS_LISTEN_PORT,
    WEBAPP_HOST,
    WEBAPP_PORT,
    WEBAPP_SSL_CERT_FILE,
    WEBAPP_SSL_KEY_FILE,
    WEBAPP_SSL_MODE,
    get_ha_auth_mode,
    has_ha_auth,
)
from ha_client import ha_poller
# Must load before importing server functions: it installs the PRO2-only
# Modbus dispatcher wrappers while leaving PRO380/Janitza untouched.
import pro2_runtime_patch  # noqa: F401
from dr_client import force_disconnect_dr, tcp_server_loop
from state import log_net, stop_event
from webapp import app

USE_RELOADER = os.environ.get("WEBAPP_USE_RELOADER", "true").strip().lower() in {"1", "true", "yes", "on"}


def _configure_runtime_logging() -> None:
    logging.getLogger("werkzeug").disabled = True
    app.logger.disabled = True


def _run_background(name, target):
    def runner():
        log_net(f"Starting thread: {name}")
        try:
            target()
        except Exception as exc:
            log_net(f"Thread {name} crashed: {exc}")
            raise

    return runner


def _shutdown_background_services(reason: str) -> None:
    log_net(f"Shutting down background services: {reason}")
    stop_event.set()
    force_disconnect_dr(reason)


def _handle_exit_signal(signum, _frame) -> None:
    _shutdown_background_services(f"signal {signum}")
    raise SystemExit(0)


def _install_shutdown_hooks() -> None:
    atexit.register(lambda: _shutdown_background_services("process exit"))

    for sig_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            signal.signal(sig, _handle_exit_signal)
        except (ValueError, OSError):
            continue


def _low_port_requires_privilege(port: int) -> bool:
    if os.name == "nt" or port >= 1024:
        return False

    sysctl_path = Path("/proc/sys/net/ipv4/ip_unprivileged_port_start")
    try:
        threshold = int(sysctl_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        threshold = 1024

    return port < threshold


def _validate_startup() -> None:
    if has_ha_auth():
        if _low_port_requires_privilege(MODBUS_LISTEN_PORT):
            message = (
                f"Modbus listener port {MODBUS_LISTEN_PORT} is privileged on Linux/WSL. "
                "Run the app with elevated privileges, grant CAP_NET_BIND_SERVICE to the Python executable, "
                "or set MODBUS_LISTEN_PORT to an unprivileged port such as 5020 in .env."
            )
            log_net(f"Startup warning: {message}")
            print(message, file=sys.stderr)
        if _low_port_requires_privilege(WEBAPP_PORT):
            message = (
                f"Web UI port {WEBAPP_PORT} is privileged on Linux/WSL. "
                "Run the app with elevated privileges, grant CAP_NET_BIND_SERVICE to the Python executable, "
                "or set WEBAPP_PORT to an unprivileged port such as 8443 in .env."
            )
            log_net(f"Startup warning: {message}")
            print(message, file=sys.stderr)
        return

    message = (
        "No Home Assistant authentication is configured. In Home Assistant add-on mode, enable the internal "
        "API proxy and use SUPERVISOR_TOKEN automatically. In standalone mode, set HA_TOKEN in the environment "
        "or in the .env file next to app.py."
    )
    log_net(f"Startup error: {message}")
    print(message, file=sys.stderr)
    raise SystemExit(1)


def _should_start_background_threads() -> bool:
    if not USE_RELOADER:
        return True
    return os.environ.get("WERKZEUG_RUN_MAIN") == "true"


def _validate_modbus_listener() -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        probe.bind((MODBUS_LISTEN_HOST, MODBUS_LISTEN_PORT))
    except PermissionError as exc:
        message = (
            f"Failed to bind Modbus listener on {MODBUS_LISTEN_HOST}:{MODBUS_LISTEN_PORT}: {exc}. "
            "Port 502 is the Modbus TCP default, but on Linux/WSL it requires elevated privileges or "
            "CAP_NET_BIND_SERVICE. Use sudo, grant the capability to the Python executable, or set "
            "MODBUS_LISTEN_PORT=5020 in .env."
        )
        log_net(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)
    except OSError as exc:
        message = f"Failed to start Modbus listener on {MODBUS_LISTEN_HOST}:{MODBUS_LISTEN_PORT}: {exc}"
        log_net(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)
    finally:
        probe.close()


def _build_web_ssl_context():
    if WEBAPP_SSL_MODE == "off":
        return None

    if WEBAPP_SSL_MODE == "adhoc":
        return "adhoc"

    cert_path = Path(WEBAPP_SSL_CERT_FILE)
    key_path = Path(WEBAPP_SSL_KEY_FILE)

    if not WEBAPP_SSL_CERT_FILE or not WEBAPP_SSL_KEY_FILE:
        message = (
            "WEBAPP_SSL_MODE=files requires both WEBAPP_SSL_CERT_FILE and WEBAPP_SSL_KEY_FILE in .env."
        )
        log_net(f"Startup error: {message}")
        print(message, file=sys.stderr)
        raise SystemExit(1)

    if not cert_path.exists() or not key_path.exists():
        message = (
            "Configured HTTPS certificate files do not exist: "
            f"cert={cert_path} key={key_path}"
        )
        log_net(f"Startup error: {message}")
        print(message, file=sys.stderr)
        raise SystemExit(1)

    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
        return context
    except ssl.SSLError as exc:
        message = f"Failed to load HTTPS certificate files: {exc}"
        log_net(f"Startup error: {message}")
        print(message, file=sys.stderr)
        raise SystemExit(1)


def main():
    _configure_runtime_logging()
    _validate_startup()
    log_net(f"Home Assistant auth mode: {get_ha_auth_mode()}")
    stop_event.clear()
    _install_shutdown_hooks()
    web_ssl_context = _build_web_ssl_context()
    if _should_start_background_threads():
        _validate_modbus_listener()
        threading.Thread(target=_run_background("ha_poller", ha_poller), daemon=True).start()
        threading.Thread(target=_run_background("tcp_server_loop", tcp_server_loop), daemon=True).start()
    else:
        log_net("Flask reloader parent process started; waiting for child process")
    web_scheme = "https" if web_ssl_context else "http"
    log_net(f"Starting Flask web app on {web_scheme}://{WEBAPP_HOST}:{WEBAPP_PORT}")
    app.run(
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        debug=False,
        use_reloader=USE_RELOADER,
        ssl_context=web_ssl_context,
    )


if __name__ == "__main__":
    main()
