#!/usr/bin/with-contenv bashio

set -euo pipefail

export PATH=/opt/venv/bin:${PATH}
export APP_ENV_FILE=/data/bmw_wallboxproxy.env
export MODBUS_LISTEN_HOST=0.0.0.0
export MODBUS_LISTEN_PORT=502
export WEBAPP_HOST=0.0.0.0
export WEBAPP_PORT=8099
export WEBAPP_SSL_MODE=off
export WEBAPP_USE_RELOADER=false
export HA_TOKEN="$(bashio::config 'ha_token')"

if [ ! -f "${APP_ENV_FILE}" ]; then
  cat > "${APP_ENV_FILE}" <<'EOF'
HA_URL=http://homeassistant.local:8123
HA_VERIFY_TLS=true
MODBUS_TRANSPORT_MODE=rtu_over_tcp
MODBUS_FLOAT_WORD_ORDER=abcd
MODBUS_REGISTER_ALIAS_MODE=exact
EOF
fi

bashio::log.info "Starting BMW Wallbox Proxy add-on"
bashio::log.info "Web UI is served over Home Assistant ingress on internal HTTP port 8099"

exec /opt/venv/bin/python /app/app.py