# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg gcc git && \
    rm -rf /var/lib/apt/lists/*

COPY packager/requirements.txt ./
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
COPY packager/packager.py ./
COPY packager/requirements.txt ./
COPY pipeline_utils /app/pipeline_utils

ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 5000

ENTRYPOINT ["python", "packager.py"]
