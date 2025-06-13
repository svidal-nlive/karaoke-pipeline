# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /app

# System dependencies for audio + git for pip git installs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        gcc \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    # numpy wheel pre-installed for Spleeter
    /venv/bin/pip install numpy==1.23.5 --only-binary=:all: && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Production image ---
FROM python:3.11-slim

WORKDIR /app

# System runtime deps only (smaller)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv

COPY splitter.py ./
COPY requirements.txt ./

ENV PATH="/venv/bin:$PATH"

EXPOSE 5000

ENTRYPOINT ["python", "splitter.py"]


