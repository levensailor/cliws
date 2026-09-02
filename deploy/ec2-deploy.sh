#!/usr/bin/env bash
# Copy CLIWS to EC2 and run install.sh over SSH.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=aws-env.sh
source "${SCRIPT_DIR}/aws-env.sh"

PUBLIC_IP="${1:-${EC2_PUBLIC_IP:-}}"
SSH_USER="${EC2_SSH_USER:-ec2-user}"
SSH_KEY_PATH="${EC2_SSH_KEY_PATH:-${HOME}/.ssh/cliws_ec2_key}"
INSTALL_DIR="${INSTALL_DIR:-/opt/cliws}"
SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -i "${SSH_KEY_PATH}")

if [[ -z "${PUBLIC_IP}" ]]; then
  echo "Usage: ec2-deploy.sh <public-ip>" >&2
  echo "Or set EC2_PUBLIC_IP." >&2
  exit 1
fi

if [[ ! -f "${SSH_KEY_PATH}" ]]; then
  echo "SSH private key not found at ${SSH_KEY_PATH}" >&2
  exit 1
fi

echo "Waiting for SSH on ${SSH_USER}@${PUBLIC_IP}..."
for attempt in $(seq 1 30); do
  if ssh "${SSH_OPTS[@]}" "${SSH_USER}@${PUBLIC_IP}" "echo ready" >/dev/null 2>&1; then
    break
  fi
  if [[ "${attempt}" -eq 30 ]]; then
    echo "SSH not available after 30 attempts." >&2
    exit 1
  fi
  sleep 10
done

echo "Bootstrapping target host..."
scp "${SSH_OPTS[@]}" "${SCRIPT_DIR}/ec2-bootstrap.sh" "${SSH_USER}@${PUBLIC_IP}:/tmp/ec2-bootstrap.sh"
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${PUBLIC_IP}" "sudo bash /tmp/ec2-bootstrap.sh"

echo "Uploading application source..."
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${PUBLIC_IP}" "sudo mkdir -p ${INSTALL_DIR} && sudo chown ${SSH_USER}:${SSH_USER} ${INSTALL_DIR}"
tar -C "${REPO_ROOT}" \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='data' \
  --exclude='logs' \
  --exclude='certs' \
  --exclude='frontend/vendor' \
  -czf /tmp/cliws-src.tgz .
scp "${SSH_OPTS[@]}" /tmp/cliws-src.tgz "${SSH_USER}@${PUBLIC_IP}:/tmp/cliws-src.tgz"
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${PUBLIC_IP}" "mkdir -p /tmp/cliws-src && tar -xzf /tmp/cliws-src.tgz -C /tmp/cliws-src"

echo "Running install.sh on target..."
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${PUBLIC_IP}" "cd /tmp/cliws-src && sudo chmod +x install.sh scripts/*.sh deploy/*.sh && sudo INSTALL_DIR=${INSTALL_DIR} ./install.sh"

echo "Verifying health endpoint..."
for attempt in $(seq 1 12); do
  if ssh "${SSH_OPTS[@]}" "${SSH_USER}@${PUBLIC_IP}" "curl -ksf https://127.0.0.1/healthz" >/dev/null 2>&1; then
    echo "Deployment healthy."
    echo "APP_URL=https://${PUBLIC_IP}/"
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
      echo "app_url=https://${PUBLIC_IP}/" >> "${GITHUB_OUTPUT}"
    fi
    exit 0
  fi
  sleep 10
done

echo "Health check failed after deployment." >&2
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${PUBLIC_IP}" "sudo systemctl status cliws --no-pager || true"
exit 1
