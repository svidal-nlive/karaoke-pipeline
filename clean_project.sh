#!/bin/bash

echo "Cleaning project: Removing build artifacts, caches, and node_modules..."

# Remove Python caches
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Remove test caches
rm -rf .pytest_cache/
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Remove node_modules and JS/React build artifacts
rm -rf dashboard/karaoke-pipeline-dashboard/node_modules/
rm -rf dashboard/karaoke-pipeline-dashboard/build/
rm -rf dashboard/karaoke-pipeline-dashboard/.next/
rm -rf dashboard/karaoke-pipeline-dashboard/.turbo/
rm -rf dashboard/karaoke-pipeline-dashboard/coverage/

# Remove env files except template/example
# find . -type f -name ".env" ! -name ".env.example" -delete

# Remove logs, temp, output, E2E runtime data
rm -rf temp_chunks/
rm -rf e2e/input/
rm -rf e2e/logs/
rm -rf e2e/metadata/
rm -rf e2e/organized/
rm -rf e2e/output/
rm -rf e2e/queue/
rm -rf e2e/stems/
rm -rf *.log

echo "Cleanup complete. Double-check 'git status' before committing."
