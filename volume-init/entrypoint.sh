#!/bin/sh
set -e

echo "🔑 [volume-init] Setting ownership of shared volumes to ${PUID}:${PGID}"

DIRS="/input /queue /logs /metadata /output /music_organized /stems /cookies /chromium_config /profile"
for path in $DIRS; do
  if [ -d "$path" ]; then
    echo " - Chowning $path"
    chown -R "${PUID}:${PGID}" "$path"
  else
    echo " - Skipping $path (not present)"
  fi
done

echo "✅ [volume-init] Volume permission setup complete."
