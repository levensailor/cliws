#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/cliws}"
SERVICE_NAME="${SERVICE_NAME:-cliws}"
SKIP_VENDOR="${SKIP_VENDOR:-0}"
PYTHON_BIN="${PYTHON_BIN:-}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

usage() {
  cat <<EOF
Usage: sudo ./install.sh [options]

Options:
  --install-dir PATH   Installation directory (default: /opt/cliws)
  --python PATH        Python interpreter (default: auto-detect >=3.10)
  --no-vendor          Skip downloading frontend vendor assets
  --help               Show this help
EOF
}

python_meets_minimum() {
  local binary="$1"
  "${binary}" -c "import sys; raise SystemExit(0 if sys.version_info >= (${MIN_PYTHON_MAJOR}, ${MIN_PYTHON_MINOR}) else 1)"
}

select_python() {
  if [[ -n "${PYTHON_BIN}" ]]; then
    if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
      echo "Configured PYTHON_BIN not found: ${PYTHON_BIN}" >&2
      exit 1
    fi
    if ! python_meets_minimum "${PYTHON_BIN}"; then
      echo "Configured PYTHON_BIN must be Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ (${PYTHON_BIN} is older)." >&2
      exit 1
    fi
    return
  fi

  local candidate
  for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "${candidate}" >/dev/null 2>&1 && python_meets_minimum "${candidate}"; then
      PYTHON_BIN="${candidate}"
      return
    fi
  done

  echo "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required (FastAPI/pydantic dependency)." >&2
  echo "Install python3.11 (or newer) and re-run install.sh." >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    --no-vendor)
      SKIP_VENDOR=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "${EUID}" -ne 0 ]]; then
  echo "install.sh must be run as root." >&2
  exit 1
fi

select_python
echo "Using Python: ${PYTHON_BIN} ($("${PYTHON_BIN}" --version 2>&1))"

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required for TLS certificate generation." >&2
  exit 1
fi

echo "Copying application files..."
mkdir -p "${INSTALL_DIR}"
cp -a "${SOURCE_DIR}/." "${INSTALL_DIR}/"
rm -rf "${INSTALL_DIR}/.git" "${INSTALL_DIR}/.venv" "${INSTALL_DIR}/data" "${INSTALL_DIR}/logs" "${INSTALL_DIR}/certs"

if [[ "${SKIP_VENDOR}" -eq 0 ]]; then
  APP_DIR="${INSTALL_DIR}" bash "${INSTALL_DIR}/scripts/fetch_vendor.sh"
else
  echo "Skipping vendor download (--no-vendor)."
fi

if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
  cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
  sed -i "s|CLIWS_APP_DIR=.*|CLIWS_APP_DIR=${INSTALL_DIR}|g" "${INSTALL_DIR}/.env"
  sed -i "s|CLIWS_SSL_CERTFILE=.*|CLIWS_SSL_CERTFILE=${INSTALL_DIR}/certs/cliws.crt|g" "${INSTALL_DIR}/.env"
  sed -i "s|CLIWS_SSL_KEYFILE=.*|CLIWS_SSL_KEYFILE=${INSTALL_DIR}/certs/cliws.key|g" "${INSTALL_DIR}/.env"
fi

"${PYTHON_BIN}" -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

mkdir -p "${INSTALL_DIR}/data" "${INSTALL_DIR}/logs" "${INSTALL_DIR}/certs"

DB_FILE="${INSTALL_DIR}/data/cliws.db"
if [[ ! -f "${DB_FILE}" ]]; then
  echo "Initializing SQLite database..."
  sqlite3 "${DB_FILE}" < "${INSTALL_DIR}/sql/001_init.sql"
  sqlite3 "${DB_FILE}" < "${INSTALL_DIR}/sql/002_seed.sql"
fi

if [[ ! -f "${INSTALL_DIR}/certs/cliws.crt" || ! -f "${INSTALL_DIR}/certs/cliws.key" ]]; then
  bash "${INSTALL_DIR}/deploy/gen_cert.sh" "${INSTALL_DIR}"
fi

# shellcheck disable=SC1091
set -a
source "${INSTALL_DIR}/.env"
set +a

SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
sed \
  -e "s|{{INSTALL_DIR}}|${INSTALL_DIR}|g" \
  -e "s|{{CLIWS_HOST}}|${CLIWS_HOST}|g" \
  -e "s|{{CLIWS_PORT}}|${CLIWS_PORT}|g" \
  -e "s|{{CLIWS_SSL_CERTFILE}}|${CLIWS_SSL_CERTFILE}|g" \
  -e "s|{{CLIWS_SSL_KEYFILE}}|${CLIWS_SSL_KEYFILE}|g" \
  "${INSTALL_DIR}/deploy/cliws.service" > "${SERVICE_PATH}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

open_firewall() {
  local port="${CLIWS_PORT}"
  if command -v ufw >/dev/null 2>&1 && ufw status | grep -qi active; then
    ufw allow "${port}/tcp" || true
  elif command -v firewall-cmd >/dev/null 2>&1; then
    firewall-cmd --permanent --add-port="${port}/tcp" || true
    firewall-cmd --reload || true
  elif command -v iptables >/dev/null 2>&1; then
    iptables -I INPUT -p tcp --dport "${port}" -j ACCEPT || true
  fi
}

open_firewall

PRIMARY_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
cat <<EOF

CLIWS installed successfully.

Service:  systemctl status ${SERVICE_NAME}
URL:      https://${PRIMARY_IP}:${CLIWS_PORT}/
Health:   https://${PRIMARY_IP}:${CLIWS_PORT}/healthz

Verify listener:
  ss -lntp | grep :${CLIWS_PORT}

If another service already uses port 443, stop it or change CLIWS_PORT in ${INSTALL_DIR}/.env
and re-run: systemctl restart ${SERVICE_NAME}

EOF
