#!/bin/bash
# Add ".venv" to all .dockerignore files recursively if not present

find . -name ".dockerignore" | while read -r ignorefile; do
  # Check if .venv is already present
  if ! grep -qxF ".venv" "$ignorefile"; then
    echo ".venv" >> "$ignorefile"
    echo "Added .venv to $ignorefile"
  else
    echo ".venv already present in $ignorefile"
  fi
done
