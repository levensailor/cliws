#!/usr/bin/env bash
# Install OS packages required by install.sh on Amazon Linux 2023.
set -euo pipefail

if command -v dnf >/dev/null 2>&1; then
  dnf update -y
  dnf install -y python3 python3-pip sqlite openssl curl unzip tar git rsync
elif command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y python3 python3-pip python3-venv sqlite3 openssl curl unzip tar git rsync
else
  echo "Unsupported Linux distribution for bootstrap." >&2
  exit 1
fi

python3 --version
sqlite3 --version || true
openssl version
