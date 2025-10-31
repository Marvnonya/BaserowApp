#!/bin/bash
set -euo pipefail

echo "[entrypoint] SHORTLINK=${SHORTLINK:-<not-set>}"

# Default command if none provided
if [ $# -eq 0 ]; then
  set -- buildozer android debug
fi

# If running as root, try to chown the mounted app folder (if possible),
# then run the command as builduser while explicitly exporting the venv PATH.
if [ "$(id -u)" -eq 0 ]; then
  echo "[entrypoint] running as root — attempting chown of /home/builduser/app ..."
  chown -R builduser:builduser /home/builduser/app 2>/dev/null || true

  # Build command as a string
  CMD="$*"

  # Run as builduser but ensure venv bin is in PATH
  exec su builduser -s /bin/bash -c "export PATH=/home/builduser/.venv/bin:\$PATH; $CMD"
else
  # already non-root: ensure PATH then exec
  export PATH="/home/builduser/.venv/bin:${PATH}"
  exec "$@"
fi
