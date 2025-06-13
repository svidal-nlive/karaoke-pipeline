#!/bin/bash
set -euo pipefail

# ---- Configurable Paths ----
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
E2E_COMPOSE="e2e/docker-compose.e2e.yml"
MAIN_COMPOSE="docker-compose.yml"
METADATA_JSON_DIR="${PROJECT_ROOT}/metadata"

# ---- 1. Clean old containers, networks, and volumes ----
echo "[1/6] Shutting down and cleaning Docker volumes/containers..."
docker compose -f "$MAIN_COMPOSE" -f "$E2E_COMPOSE" down -v

echo "[2/6] Cleaning pipeline folders..."
for dir in input output stems queue logs organized; do
  rm -rf "${PROJECT_ROOT}/${dir:?}"/*
done
rm -rf "$METADATA_JSON_DIR"/*
mkdir -p "$METADATA_JSON_DIR"

# ---- 2. Build images from scratch ----
echo "[3/6] Building all Docker images (no cache)..."
docker compose -f "$MAIN_COMPOSE" -f "$E2E_COMPOSE" build --no-cache

# ---- 3. Initialize volume permissions ----
echo "[4/6] Running volume-init for permissions..."
docker compose -f "$MAIN_COMPOSE" -f "$E2E_COMPOSE" run --rm volume-init

# ---- 4. Start up the pipeline stack ----
echo "[5/6] Starting the pipeline stack in background..."
docker compose -f "$MAIN_COMPOSE" -f "$E2E_COMPOSE" up -d

# ---- 5. Wait for status-api health ----
echo "[6/6] Waiting for status-api /health endpoint..."
for i in {1..60}; do
  if curl -sf http://localhost:5001/health > /dev/null; then
    echo "status-api is up."
    break
  fi
  sleep 2
done

# ---- 6. Run E2E pytest ----
echo "Running e2e/test_pipeline_e2e.py ..."
pytest e2e/test_pipeline_e2e.py

echo "E2E pipeline test complete."

# ---- 7. (Optional) Show summary logs ----
docker compose -f "$MAIN_COMPOSE" -f "$E2E_COMPOSE" logs --tail=80

echo "Done. Clean up with:"
echo "docker compose -f $MAIN_COMPOSE -f $E2E_COMPOSE down -v"
