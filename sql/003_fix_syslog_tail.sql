-- Fix SYSLOG TAIL for Amazon Linux / journald hosts where
-- /var/log/syslog and /var/log/messages do not exist.
--
-- Manual apply on the server:
--   sudo sqlite3 /opt/cliws/data/cliws.db < /opt/cliws/sql/003_fix_syslog_tail.sql
--   (or edit the entry in the UI)

UPDATE entries
SET cmd = 'if [ -f /var/log/syslog ]; then tail -f /var/log/syslog; elif [ -f /var/log/messages ]; then tail -f /var/log/messages; else journalctl -f -n 50; fi'
WHERE name = 'SYSLOG TAIL';
