#!/bin/bash
set -e

BASE="pipeline-data"
DIRS=(input queue stems output organized metadata logs)

mkdir -p "$BASE"
for d in "${DIRS[@]}"; do
  mkdir -p "$BASE/$d"
  echo "Created: $BASE/$d"
done

echo "All pipeline-data subdirectories created."
