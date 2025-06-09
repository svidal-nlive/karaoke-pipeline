#!/usr/bin/env bash

set -e

find . -name requirements.txt | while read -r reqfile; do
  # Remove any existing setuptools or pip lines to avoid duplicates
  grep -v -i '^setuptools' "$reqfile" | grep -v -i '^pip' > "$reqfile.tmp"
  # Prepend setuptools>=68.0 and pip>=23.2
  printf "setuptools>=68.0\npip>=23.2\n" | cat - "$reqfile.tmp" > "$reqfile"
  rm "$reqfile.tmp"
  echo "Updated $reqfile with setuptools>=68.0 and pip>=23.2"
done
