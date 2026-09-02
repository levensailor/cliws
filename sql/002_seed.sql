-- Seed data for CLIWS dashboard
INSERT INTO sections (id, name, layout, position) VALUES
    (1, 'SYSTEM', 'grid', 0),
    (2, 'MAINTENANCE', 'list', 1);

INSERT INTO subsections (id, section_id, name, position) VALUES
    (1, 1, 'OVERVIEW', 0),
    (2, 2, 'LOGS', 0),
    (3, 2, 'DOCKER', 1),
    (4, 2, 'NETWORK', 2);

INSERT INTO entries (subsection_id, name, cmd, icon, position) VALUES
    (1, 'UPTIME', 'uptime', 'fa-solid fa-clock', 0),
    (1, 'DISK USAGE', 'df -h', 'fa-solid fa-hard-drive', 1),
    (1, 'INTERFACES', 'ip -br a', 'fa-solid fa-network-wired', 2),
    (1, 'LISTENING PORTS', 'ss -lntp', 'fa-solid fa-plug', 3),
    (2, 'JOURNAL FOLLOW', 'journalctl -f -n 50', 'fa-solid fa-scroll', 0),
    (2, 'SYSLOG TAIL', 'if [ -f /var/log/syslog ]; then tail -f /var/log/syslog; elif [ -f /var/log/messages ]; then tail -f /var/log/messages; else journalctl -f -n 50; fi', 'fa-solid fa-file-lines', 1),
    (3, 'DOCKER STATS', 'docker stats --no-stream && docker stats', 'fa-brands fa-docker', 0),
    (3, 'DOCKER PS', 'docker ps -a', 'fa-solid fa-box', 1),
    (4, 'PING GATEWAY', 'ping -c 4 $(ip route | awk ''/default/ {print $3; exit}'')', 'fa-solid fa-wifi', 0),
    (4, 'DNS LOOKUP', 'dig +short google.com || nslookup google.com', 'fa-solid fa-globe', 1);

INSERT INTO settings (key, value) VALUES
    ('greeting_enabled', 'true'),
    ('theme', 'one-dark');

PRAGMA user_version = 2;
