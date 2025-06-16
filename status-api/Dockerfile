# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc git && rm -rf /var/lib/apt/lists/*

COPY status-api/requirements.txt ./
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /venv /venv
COPY status-api/status_api.py ./
COPY status-api/requirements.txt ./
COPY pipeline_utils /app/pipeline_utils

ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 5001

ENTRYPOINT ["python", "status_api.py"]
