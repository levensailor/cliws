## Learned User Preferences

- Prefer a Python FastAPI backend (pydantic, uvicorn, python-dotenv) unless specified otherwise.
- After code changes, commit with a relevant message and push to `main`; do not run the app locally or deploy over SSH—CI/CD builds and deploys automatically.
- Accept no in-app authentication and root command execution for this private VLAN / home-lab app; network security is handled outside the server.
- Keep all durable storage under the application directory; SQLite is acceptable.
- When a SQL update is required, add a SQL script file for the user to run manually.
- Match the Flame start-page look (One Dark palette) for the dashboard UI.
- Prefer free-tier-friendly EC2 (`t3.micro`) with a public IP and a security group opening SSH and HTTPS.

## Learned Workspace Facts

- CLIWS is a curated, clickable CLI dashboard: Flame-style sections/entries, edit mode, Font Awesome icon picker, and live PTY output over WebSockets into a bottom xterm drawer.
- Default install path is `/opt/cliws`; `install.sh` sets up a root systemd service serving HTTPS on `0.0.0.0:443` with self-signed certs under `certs/`.
- Frontend is no-build vanilla HTML/CSS/JS; vendor assets (xterm, Font Awesome) are fetched by `scripts/fetch_vendor.sh` during install.
- GitHub Actions deploy uses environment `main` with `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `EC2_SSH_PRIVATE_KEY`; `EC2_KEY_NAME` selects the existing EC2 key pair; target is Amazon Linux 2023.
- Amazon Linux 2023 defaults to Python 3.9—bootstrap/install must use Python 3.11+ for current FastAPI; AL2023 ships `curl-minimal` (do not install conflicting full `curl`); system logs are journald-based (`/var/log/messages` often missing).
- xterm.js UMD FitAddon exposes a nested constructor (`FitAddon.FitAddon`), not `FitAddon` itself as the constructor.
- Browser WebSockets use `wss://` on the same host and port as HTTPS (`/ws/run`); no separate WebSocket port or ALB is required for direct-to-instance EC2.
- Schema changes are manual SQL under `sql/`; the app checks `PRAGMA user_version` against `CLIWS_SCHEMA_VERSION`.
