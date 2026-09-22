#!/bin/bash
# ==============================================================================
# kiw-excel - Helper Script to Synchronize Department Accounts
# Dapat dijalankan langsung di host atau via docker compose
# ==============================================================================
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DIR")"

echo "==> Menyelaraskan akun departemen kiw-excel..."

if command -v python3 >/dev/null 2>&1; then
  python3 "${DIR}/init_users.py"
elif docker compose version >/dev/null 2>&1; then
  docker compose exec backup python3 /usr/local/bin/init_users.py
else
  echo "Error: Python3 atau Docker Compose tidak ditemukan."
  exit 1
fi

echo "==> Selesai."
