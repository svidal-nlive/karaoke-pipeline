#!/usr/bin/env bash
set -e

echo "🧹 Cleaning up all containers, volumes, and networks..."
docker compose -f docker-compose.yml -f e2e/docker-compose.e2e.yml down -v || true

echo "🐳 Building all services..."
docker compose -f docker-compose.yml -f e2e/docker-compose.e2e.yml build --pull

echo "🔑 Ensuring volumes/permissions..."
docker compose -f docker-compose.yml -f e2e/docker-compose.e2e.yml run --rm volume-init

echo "🚀 Starting pipeline stack in background..."
docker compose -f docker-compose.yml -f e2e/docker-compose.e2e.yml up -d

echo "🧪 Running E2E tests..."
pytest e2e/test_pipeline_e2e.py

echo "🧹 Cleaning up after test run..."
docker compose -f docker-compose.yml -f e2e/docker-compose.e2e.yml down -v

echo "✅ CI E2E pipeline complete!"
