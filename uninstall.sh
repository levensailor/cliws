#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/cliws}"
SERVICE_NAME="${SERVICE_NAME:-cliws}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "uninstall.sh must be run as root." >&2
  exit 1
fi

systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
systemctl disable "${SERVICE_NAME}" 2>/dev/null || true
rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload

read -r -p "Remove application directory ${INSTALL_DIR}? [y/N] " reply
if [[ "${reply}" =~ ^[Yy]$ ]]; then
  rm -rf "${INSTALL_DIR}"
  echo "Removed ${INSTALL_DIR}"
else
  echo "Left ${INSTALL_DIR} in place."
fi

echo "CLIWS uninstalled."
