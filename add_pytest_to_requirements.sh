#!/bin/bash
set -e

PYTEST_PACKAGES="# Test dependencies
pytest
pytest-mock"

# Find all requirements.txt files recursively (excluding venv, hidden, etc)
find . -type f -name requirements.txt | while read -r REQ; do
    # Skip if inside a .venv or hidden dir
    if [[ "$REQ" == *".venv"* ]] || [[ "$REQ" == *"/."* ]]; then
        continue
    fi
    # Check if pytest is already present (case-insensitive)
    if grep -i -q "^pytest" "$REQ"; then
        echo "[✓] pytest already present in $REQ"
    else
        echo -e "\n$PYTEST_PACKAGES" >> "$REQ"
        echo "[+] Added pytest and pytest-mock to $REQ"
    fi
done

echo "Pytest dependencies ensured for all requirements.txt files recursively."
