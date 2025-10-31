#!/bin/bash
# /usr/local/bin/entrypoint.sh

# Shortlink aus Environment
echo "SHORTLINK=${SHORTLINK:-<not-set>}"

# Wenn wir als root starten, versuche Ownership zu setzen
if [ "$(id -u)" -eq 0 ]; then
    echo "[INFO] Running as root, fixing permissions..."
    chown -R builduser:builduser /home/builduser/app 2>/dev/null || true
    exec su - builduser -c "$*"
else
    # Bereits non-root, direkt ausführen
    exec "$@"
fi
