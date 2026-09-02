#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-/opt/cliws}"
CERT_DIR="${APP_DIR}/certs"
CERT_FILE="${CERT_DIR}/cliws.crt"
KEY_FILE="${CERT_DIR}/cliws.key"
DAYS="${CERT_DAYS:-3650}"
CN="${CERT_CN:-cliws.local}"

mkdir -p "${CERT_DIR}"

HOSTNAME_FQDN="$(hostname -f 2>/dev/null || hostname)"
HOSTNAME_SHORT="$(hostname -s 2>/dev/null || hostname)"
IP_ADDRS="$(hostname -I 2>/dev/null || true)"

SAN_ENTRIES="DNS:${CN},DNS:${HOSTNAME_FQDN},DNS:${HOSTNAME_SHORT},DNS:localhost,IP:127.0.0.1"
for ip in ${IP_ADDRS}; do
  SAN_ENTRIES="${SAN_ENTRIES},IP:${ip}"
done

OPENSSL_CNF="${CERT_DIR}/openssl.cnf"
cat > "${OPENSSL_CNF}" <<EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
CN = ${CN}

[v3_req]
subjectAltName = ${SAN_ENTRIES}
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
EOF

openssl req -x509 -nodes -newkey rsa:4096 \
  -keyout "${KEY_FILE}" \
  -out "${CERT_FILE}" \
  -days "${DAYS}" \
  -config "${OPENSSL_CNF}"

chmod 600 "${KEY_FILE}"
chmod 644 "${CERT_FILE}"

echo "Generated certificate:"
echo "  cert: ${CERT_FILE}"
echo "  key:  ${KEY_FILE}"
echo "  SANs: ${SAN_ENTRIES}"
