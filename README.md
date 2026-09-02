# CLIWS

Curated, clickable CLI dashboard for private Linux servers. CLIWS presents a Flame-inspired start page where each tile runs a root shell command and streams live PTY output over WebSockets into a bottom terminal drawer.

**Author:** levensailor

## Description

CLIWS is a self-hosted web application for home lab VLANs. It provides:

- A dark, Flame-style dashboard of sections, subsections, and command entries
- One-click command execution with real terminal output (ANSI colors, streaming logs)
- In-page edit mode to add, rename, reorder, and delete entries without editing files
- Font Awesome icon picker with search and categories
- SQLite storage in the application directory
- HTTPS on `0.0.0.0:443` via a root systemd service (no in-app authentication)

## Public URL

After installation on your Linux host:

- Dashboard: `https://<server-ip>/`
- Health check: `https://<server-ip>/healthz`

Use the machine's VLAN IP address. The installer generates a self-signed certificate; accept the browser warning or replace the cert in `certs/`.

## Deployment

### Requirements

- Linux host (systemd)
- `python3`, `pip`, `sqlite3`, `openssl`, `curl`, `unzip`
- Root access (service runs as root to execute commands and bind port 443)

### Install

```bash
git clone <your-repo-url> cliws
cd cliws
sudo chmod +x install.sh uninstall.sh scripts/*.sh deploy/*.sh
sudo ./install.sh
```

Default install path: `/opt/cliws`

Options:

```bash
sudo ./install.sh --install-dir /opt/cliws
sudo ./install.sh --no-vendor    # skip frontend vendor download (offline/pre-seeded)
```

### Verify HTTPS on 0.0.0.0:443

```bash
sudo ss -lntp | grep :443
sudo systemctl status cliws
curl -k https://127.0.0.1/healthz
```

### Open port 443

**ufw**

```bash
sudo ufw allow 443/tcp
sudo ufw status
```

**firewalld**

```bash
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

**iptables**

```bash
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
```

If another service (nginx, caddy) already listens on 443, stop it or change `CLIWS_PORT` in `/opt/cliws/.env` and restart:

```bash
sudo systemctl restart cliws
```

### Service management

```bash
sudo systemctl status cliws
sudo systemctl restart cliws
sudo journalctl -u cliws -f
```

### Uninstall

```bash
sudo ./uninstall.sh
```

## CI/CD (GitHub Actions → EC2)

Pushes to `main` provision (or reuse) a Linux EC2 instance and deploy CLIWS automatically.

Workflow file: [`.github/workflows/deploy-ec2.yml`](.github/workflows/deploy-ec2.yml)

### Required GitHub secrets

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS access key with EC2 permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `EC2_SSH_PRIVATE_KEY` | Private key matching the EC2 key pair (PEM contents) |

### Recommended GitHub variables

| Variable | Default | Description |
|---|---|---|
| `AWS_REGION` | `us-east-1` | AWS region |
| `EC2_KEY_NAME` | *(required)* | Existing EC2 key pair name |
| `EC2_INSTANCE_TYPE` | `t3.micro` | Instance size (free-tier friendly) |
| `EC2_INSTANCE_NAME` | `cliws` | Name tag used to reuse the same VM |
| `EC2_FORCE_NEW_INSTANCE` | `false` | Set `true` to terminate and recreate |

### What the pipeline does

1. Authenticates with `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
2. Creates (or reuses) a security group allowing SSH (`22`) and HTTPS (`443`) from `0.0.0.0/0`
3. Launches Amazon Linux 2023 with a public IP (`t3.micro` by default)
4. Copies the repo over SSH and runs `install.sh`
5. Verifies `https://<public-ip>/healthz`

Manual redeploy with a fresh VM:

```text
GitHub → Actions → Deploy to EC2 → Run workflow → force_new_instance = true
```

### IAM permissions

The AWS user/role needs at minimum:

- `ec2:RunInstances`, `ec2:DescribeInstances`, `ec2:StartInstances`, `ec2:StopInstances`, `ec2:TerminateInstances`
- `ec2:CreateSecurityGroup`, `ec2:DescribeSecurityGroups`, `ec2:AuthorizeSecurityGroupIngress`, `ec2:CreateTags`
- `ec2:DescribeVpcs`, `ec2:DescribeImages`
- `ssm:GetParameters`

## Configuration

Environment file: `/opt/cliws/.env`

| Variable | Default | Description |
|---|---|---|
| `CLIWS_HOST` | `0.0.0.0` | Bind address |
| `CLIWS_PORT` | `443` | HTTPS port |
| `CLIWS_SSL_CERTFILE` | `/opt/cliws/certs/cliws.crt` | TLS certificate |
| `CLIWS_SSL_KEYFILE` | `/opt/cliws/certs/cliws.key` | TLS private key |
| `CLIWS_SHELL` | `/bin/bash` | Shell for commands |
| `CLIWS_DB_PATH` | `data/cliws.db` | SQLite database path |
| `CLIWS_RUN_RETENTION_SECONDS` | `300` | Keep finished runs in memory |

## Development notes

- Schema migrations are manual SQL files in `sql/`; the app refuses to start if `PRAGMA user_version` does not match `CLIWS_SCHEMA_VERSION`.
- Frontend vendor assets are downloaded once by `scripts/fetch_vendor.sh` during install.
- Logs: console + `/opt/cliws/logs/cliws.log` (1 MB rotation, 3 backups, EST timestamps).

## Security notice

CLIWS is designed for a trusted private VLAN with no authentication. All commands run as root. Handle network isolation and access control outside the application.
