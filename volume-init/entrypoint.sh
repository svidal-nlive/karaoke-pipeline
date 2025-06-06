#!/bin/sh
set -e

echo "Chowning all relevant mount points to ${PUID}:${PGID}..."

for path in /input /queue /logs /metadata /output /organized /stems /cookies /chromium_config /profile; do
  if [ -d "$path" ]; then
    echo " - Setting $path"
    chown -R "${PUID}:${PGID}" "$path"
  else
    echo " - Skipping $path (not present)"
  fi
done

echo "Volume init complete."
