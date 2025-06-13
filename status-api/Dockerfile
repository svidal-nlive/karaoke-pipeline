# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app

# Install gcc and git for pip install and building dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Production image ---
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /venv /venv

COPY status_api.py ./
COPY requirements.txt ./

ENV PATH="/venv/bin:$PATH"

EXPOSE 5001

ENTRYPOINT ["python", "status_api.py"]
