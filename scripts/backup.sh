#!/usr/bin/env bash
# ==============================================================================
# kiw-excel - Automated Hot Backup Script
# Transactionally safe backup for SQLite & Grist documents
# ==============================================================================
set -euo pipefail

DATA_DIR="${DATA_DIR:-/data}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
RCLONE_DEST="${RCLONE_REMOTE_DEST:-}"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_NAME="kiw-excel-backup-${TIMESTAMP}"
WORK_DIR="/tmp/${BACKUP_NAME}"
ARCHIVE_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

echo "========================================================================"
echo " [$(date +"%Y-%m-%d %H:%M:%S")] Starting kiw-excel backup: ${BACKUP_NAME}"
echo "========================================================================"

if [ ! -d "${DATA_DIR}" ]; then
  echo "ERROR: Data directory ${DATA_DIR} does not exist!" >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"
rm -rf "${WORK_DIR}"
mkdir -p "${WORK_DIR}/docs" "${WORK_DIR}/auth" "${WORK_DIR}/params"

# 1. Hot backup SQLite home metadata database
if [ -f "${DATA_DIR}/home.sqlite3" ]; then
  echo "--> Performing safe hot backup of home.sqlite3..."
  sqlite3 "${DATA_DIR}/home.sqlite3" ".backup '${WORK_DIR}/home.sqlite3'"
fi

# 2. Hot backup Dex authentication database
if [ -f "${DATA_DIR}/auth/dex.db" ]; then
  echo "--> Performing safe hot backup of dex.db..."
  sqlite3 "${DATA_DIR}/auth/dex.db" ".backup '${WORK_DIR}/auth/dex.db'"
fi

# 3. Hot backup session database if present
if [ -f "${DATA_DIR}/grist-sessions.db" ]; then
  echo "--> Backing up grist-sessions.db..."
  sqlite3 "${DATA_DIR}/grist-sessions.db" ".backup '${WORK_DIR}/grist-sessions.db'"
fi

# 4. Hot backup all Grist spreadsheet documents (.grist SQLite files)
DOC_COUNT=0
if [ -d "${DATA_DIR}/docs" ]; then
  for doc in "${DATA_DIR}/docs"/*.grist; do
    if [ -f "$doc" ]; then
      DOC_FILENAME=$(basename "$doc")
      sqlite3 "$doc" ".backup '${WORK_DIR}/docs/${DOC_FILENAME}'"
      DOC_COUNT=$((DOC_COUNT + 1))
    fi
  done
fi
echo "--> Safely backed up ${DOC_COUNT} spreadsheet document(s)."

# 5. Backup encryption params & tokens
if [ -d "${DATA_DIR}/params" ]; then
  cp -r "${DATA_DIR}/params"/* "${WORK_DIR}/params/" 2>/dev/null || true
fi

# 6. Save backup metadata
cat <<EOF > "${WORK_DIR}/backup-meta.json"
{
  "app": "kiw-excel",
  "timestamp": "${TIMESTAMP}",
  "documents_count": ${DOC_COUNT},
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

# 7. Compress into archive
echo "--> Compressing archive into ${ARCHIVE_FILE}..."
tar -czf "${ARCHIVE_FILE}" -C "/tmp" "${BACKUP_NAME}"
rm -rf "${WORK_DIR}"

# 8. Create SHA256 checksum
(cd "${BACKUP_DIR}" && sha256sum "${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.tar.gz.sha256")

ARCHIVE_SIZE=$(du -h "${ARCHIVE_FILE}" | cut -f1)
echo "--> Backup completed successfully! Size: ${ARCHIVE_SIZE}"

# 9. Optional: Cloud / Remote Sync via Rclone
if [ -n "${RCLONE_DEST}" ]; then
  if command -v rclone >/dev/null 2>&1 && [ -f "/root/.config/rclone/rclone.conf" ]; then
    echo "--> Syncing backup to remote storage (${RCLONE_DEST})..."
    rclone copy "${ARCHIVE_FILE}" "${RCLONE_DEST}"
    rclone copy "${ARCHIVE_FILE}.sha256" "${RCLONE_DEST}"
    echo "--> Remote sync successful."
  else
    echo "WARNING: RCLONE_REMOTE_DEST set but rclone or rclone.conf not found. Skipping remote upload."
  fi
fi

# 10. Clean up old local backups based on retention days
if [ "${RETENTION_DAYS}" -gt 0 ]; then
  echo "--> Cleaning up local backups older than ${RETENTION_DAYS} days..."
  find "${BACKUP_DIR}" -name "kiw-excel-backup-*.tar.gz" -mtime +"${RETENTION_DAYS}" -delete || true
  find "${BACKUP_DIR}" -name "kiw-excel-backup-*.tar.gz.sha256" -mtime +"${RETENTION_DAYS}" -delete || true
fi

echo "========================================================================"
echo " [$(date +"%Y-%m-%d %H:%M:%S")] Backup finished successfully."
echo "========================================================================"
