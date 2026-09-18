#!/usr/bin/env bash
# ==============================================================================
# kiw-excel - Safe Restore Script
# Restores Grist metadata, Dex auth, and spreadsheet documents from a backup archive
# ==============================================================================
set -euo pipefail

BACKUP_ARCHIVE="${1:-}"
TARGET_DATA_DIR="${DATA_DIR:-./grist-data}"
FORCE="${2:-}"

if [ -z "${BACKUP_ARCHIVE}" ]; then
  echo "Usage: $0 <path-to-backup-archive.tar.gz> [--yes]"
  echo "Example: $0 ./backups/kiw-excel-backup-2026-09-18_12-00-00.tar.gz"
  exit 1
fi

if [ ! -f "${BACKUP_ARCHIVE}" ]; then
  echo "ERROR: Backup archive '${BACKUP_ARCHIVE}' does not exist!" >&2
  exit 1
fi

# Optional checksum verification
if [ -f "${BACKUP_ARCHIVE}.sha256" ]; then
  echo "--> Verifying SHA256 checksum..."
  ARCHIVE_DIR=$(dirname "${BACKUP_ARCHIVE}")
  ARCHIVE_NAME=$(basename "${BACKUP_ARCHIVE}")
  (cd "${ARCHIVE_DIR}" && sha256sum -c "${ARCHIVE_NAME}.sha256")
  echo "--> Checksum OK."
fi

echo "========================================================================"
echo " RESTORE WARNING:"
echo " This operation will restore data from '${BACKUP_ARCHIVE}'"
echo " into '${TARGET_DATA_DIR}'."
echo "========================================================================"

if [ "${FORCE}" != "--yes" ] && [ "${FORCE}" != "-y" ]; then
  read -r -p "Are you sure you want to proceed with restore? (y/N): " CONFIRM
  if [[ ! "${CONFIRM}" =~ ^[yY](es)?$ ]]; then
    echo "Restore cancelled."
    exit 0
  fi
fi

TEMP_EXTRACT=$(mktemp -d /tmp/kiw_restore_XXXXXX)
trap 'rm -rf "${TEMP_EXTRACT}"' EXIT

echo "--> Extracting backup archive..."
tar -xzf "${BACKUP_ARCHIVE}" -C "${TEMP_EXTRACT}"

# Find extracted folder
EXTRACTED_FOLDER=$(find "${TEMP_EXTRACT}" -mindepth 1 -maxdepth 1 -type d | head -n 1)

if [ -z "${EXTRACTED_FOLDER}" ] || [ ! -d "${EXTRACTED_FOLDER}" ]; then
  echo "ERROR: Corrupt archive or invalid directory structure!" >&2
  exit 1
fi

# Create target directories
mkdir -p "${TARGET_DATA_DIR}/docs" "${TARGET_DATA_DIR}/auth" "${TARGET_DATA_DIR}/params"

echo "--> Restoring database and documents..."
if [ -f "${EXTRACTED_FOLDER}/home.sqlite3" ]; then
  cp -f "${EXTRACTED_FOLDER}/home.sqlite3" "${TARGET_DATA_DIR}/home.sqlite3"
fi

if [ -f "${EXTRACTED_FOLDER}/auth/dex.db" ]; then
  cp -f "${EXTRACTED_FOLDER}/auth/dex.db" "${TARGET_DATA_DIR}/auth/dex.db"
fi

if [ -f "${EXTRACTED_FOLDER}/grist-sessions.db" ]; then
  cp -f "${EXTRACTED_FOLDER}/grist-sessions.db" "${TARGET_DATA_DIR}/grist-sessions.db"
fi

if [ -d "${EXTRACTED_FOLDER}/docs" ]; then
  cp -rf "${EXTRACTED_FOLDER}/docs"/* "${TARGET_DATA_DIR}/docs/" 2>/dev/null || true
fi

if [ -d "${EXTRACTED_FOLDER}/params" ]; then
  cp -rf "${EXTRACTED_FOLDER}/params"/* "${TARGET_DATA_DIR}/params/" 2>/dev/null || true
fi

# Ensure permissions so Grist container can read and write
chmod -R a+rw "${TARGET_DATA_DIR}" 2>/dev/null || true

echo "========================================================================"
echo " Restore completed successfully!"
echo " Please restart your containers: docker compose restart grist"
echo "========================================================================"
