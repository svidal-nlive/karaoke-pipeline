# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc git && rm -rf /var/lib/apt/lists/*

COPY organizer/requirements.txt ./
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /venv /venv
COPY organizer/organizer.py ./
COPY organizer/requirements.txt ./
COPY pipeline_utils /app/pipeline_utils

ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 5000

ENTRYPOINT ["python", "organizer.py"]
