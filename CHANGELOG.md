# Changelog

All notable feature changes are documented here with timestamps.

## 2026-09-01

- Require Python 3.10+ for FastAPI; bootstrap Amazon Linux with python3.11 and auto-select a compatible interpreter in install.sh.
- Fix EC2 deploy workflow: use Node 24-compatible actions (checkout v5, configure-aws-credentials v6), bind the `main` GitHub environment, and resolve AWS credentials from environment secrets/variables.
- Add GitHub Actions EC2 deployment workflow using `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to provision a Linux VM and run `install.sh`.
- Initial CLIWS release: Flame-style curated command dashboard with WebSocket PTY streaming, edit mode, icon picker, SQLite storage, HTTPS systemd service on 0.0.0.0:443, and install.sh deployment script.
