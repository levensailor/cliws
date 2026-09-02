#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
VENDOR_DIR="${APP_DIR}/frontend/vendor"

XTERM_VERSION="${XTERM_VERSION:-6.0.0}"
XTERM_FIT_VERSION="${XTERM_FIT_VERSION:-0.11.0}"
XTERM_WEB_LINKS_VERSION="${XTERM_WEB_LINKS_VERSION:-0.12.0}"
FONTAWESOME_VERSION="${FONTAWESOME_VERSION:-6.7.2}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

mkdir -p "${VENDOR_DIR}/xterm" "${VENDOR_DIR}/fontawesome" "${VENDOR_DIR}/icons"

echo "Downloading xterm.js ${XTERM_VERSION}..."
curl -fsSL "https://cdn.jsdelivr.net/npm/@xterm/xterm@${XTERM_VERSION}/lib/xterm.js" \
  -o "${VENDOR_DIR}/xterm/xterm.js"
curl -fsSL "https://cdn.jsdelivr.net/npm/@xterm/xterm@${XTERM_VERSION}/css/xterm.css" \
  -o "${VENDOR_DIR}/xterm/xterm.css"
curl -fsSL "https://cdn.jsdelivr.net/npm/@xterm/addon-fit@${XTERM_FIT_VERSION}/lib/addon-fit.js" \
  -o "${VENDOR_DIR}/xterm/addon-fit.js"
curl -fsSL "https://cdn.jsdelivr.net/npm/@xterm/addon-web-links@${XTERM_WEB_LINKS_VERSION}/lib/addon-web-links.js" \
  -o "${VENDOR_DIR}/xterm/addon-web-links.js"

echo "Downloading Font Awesome ${FONTAWESOME_VERSION}..."
FA_ZIP="${TMP_DIR}/fontawesome.zip"
curl -fsSL "https://github.com/FortAwesome/Font-Awesome/releases/download/${FONTAWESOME_VERSION}/fontawesome-free-${FONTAWESOME_VERSION}-web.zip" \
  -o "${FA_ZIP}"
unzip -q "${FA_ZIP}" -d "${TMP_DIR}"
FA_ROOT="${TMP_DIR}/fontawesome-free-${FONTAWESOME_VERSION}-web"
cp -R "${FA_ROOT}/css" "${VENDOR_DIR}/fontawesome/"
cp -R "${FA_ROOT}/webfonts" "${VENDOR_DIR}/fontawesome/"

echo "Building icon index..."
python3 "${SCRIPT_DIR}/build_icon_index.py" \
  "${FA_ROOT}/metadata/icons.json" \
  "${VENDOR_DIR}/icons/index.json"

echo "Vendor assets installed to ${VENDOR_DIR}"
