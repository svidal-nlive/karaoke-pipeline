# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg \
      libsndfile1 \
      git \
      gcc \
    && rm -rf /var/lib/apt/lists/*

COPY splitter/requirements.txt ./
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    /venv/bin/pip install \
      torch==2.6.0 \
      torchvision==0.21.0 \
      torchaudio==2.6.0 \
      --index-url https://download.pytorch.org/whl/cpu && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
COPY splitter/splitter.py ./
COPY splitter/requirements.txt ./
COPY pipeline_utils /app/pipeline_utils

ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 5000

ENTRYPOINT ["python", "splitter.py"]
