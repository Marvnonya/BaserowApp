#!/bin/bash
# /usr/local/bin/entrypoint.sh

set -euo pipefail

echo "[entrypoint] SHORTLINK=${SHORTLINK:-<not-set>}"

# Wenn root, versuche Besitz des mount-Pfades zu übernehmen (falls möglich)
if [ "$(id -u)" -eq 0 ]; then
    echo "[entrypoint] running as root — attempting chown of /home/builduser/app ..."
    chown -R builduser:builduser /home/builduser/app 2>/dev/null || true
    # Führe Kommando als builduser aus (ohne '-' um PATH intakt zu lassen)
    exec su builduser -c "$@"
else
    echo "[entrypoint] running as non-root (uid $(id -u)) — executing command directly"
    exec "$@"
fi
