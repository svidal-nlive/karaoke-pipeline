# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app

# Install pip and build dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install in a virtualenv for smaller final image
COPY requirements.txt ./
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip setuptools wheel \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Production image ---
FROM python:3.11-slim

WORKDIR /app

# Copy venv from builder stage
COPY --from=builder /venv /venv

# Copy source files
COPY watcher.py ./
COPY requirements.txt ./

ENV PATH="/venv/bin:$PATH"

EXPOSE 5000

ENTRYPOINT ["python", "watcher.py"]
