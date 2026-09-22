#!/bin/sh
# ==============================================================================
# Backup Container Entrypoint & Cron Daemon
# ==============================================================================
set -eu

CRON_SCHEDULE="${BACKUP_CRON:-0 2 * * *}"
TIMEZONE="${TZ:-Asia/Jakarta}"

echo "========================================================================"
echo " Starting kiw-excel automated backup service"
echo " Timezone: ${TIMEZONE}"
echo " Schedule: ${CRON_SCHEDULE}"
echo " Retention: ${BACKUP_RETENTION_DAYS:-14} days"
echo " Destination: /backups"
echo "========================================================================"

# Configure timezone
if [ -f "/usr/share/zoneinfo/${TIMEZONE}" ]; then
  cp "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime
  echo "${TIMEZONE}" > /etc/timezone
fi

# Ensure required packages exist
if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "Installing required packages (sqlite, bash, rclone, coreutils)..."
  apk add --no-cache sqlite bash tzdata tar gzip coreutils rclone findutils
fi

BACKUP_BIN="/scripts/backup.sh"
if [ ! -f "$BACKUP_BIN" ]; then
  BACKUP_BIN="/usr/local/bin/backup.sh"
fi
chmod +x "$BACKUP_BIN" 2>/dev/null || true

# Synchronize department accounts and team memberships
INIT_USERS_BIN="/scripts/init_users.py"
if [ ! -f "$INIT_USERS_BIN" ]; then
  INIT_USERS_BIN="/usr/local/bin/init_users.py"
fi
if [ -f "$INIT_USERS_BIN" ] && command -v python3 >/dev/null 2>&1; then
  echo "--> Checking and synchronizing team accounts..."
  python3 "$INIT_USERS_BIN" || true
fi

# Run backup on container startup if requested
if [ "${BACKUP_ON_STARTUP:-true}" = "true" ]; then
  echo "--> Running initial startup backup..."
  "$BACKUP_BIN" || echo "Startup backup finished with warnings."
fi

# Register cron task
echo "${CRON_SCHEDULE} ${BACKUP_BIN} >> /var/log/backup.log 2>&1" > /etc/crontabs/root

echo "--> Cron schedule registered (${CRON_SCHEDULE}). Starting cron daemon..."
exec crond -f -l 2
