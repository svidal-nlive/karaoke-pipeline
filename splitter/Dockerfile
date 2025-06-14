# syntax=docker/dockerfile:1

# --- Builder stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps for audio processing and git for pip installs 
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg \
      libsndfile1 \
      git \
      gcc \
    && rm -rf /var/lib/apt/lists/*

# copy and install Python deps into a venv
COPY requirements.txt ./
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    # 1) install CPU-only PyTorch wheels
    /venv/bin/pip install \
      torch==2.6.0 \
      torchvision==0.21.0 \
      torchaudio==2.6.0 \
      --index-url https://download.pytorch.org/whl/cpu && \
    # 2) install the rest of your requirements
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Production stage ---
FROM python:3.11-slim

WORKDIR /app

# only runtime deps: ffmpeg & libsndfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg \
      libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# bring in our venv from builder
COPY --from=builder /venv /venv

# copy the splitter script and pin requirements file (for metadata/reference)
COPY splitter.py requirements.txt ./

# ensure we use the venv’s python & pip
ENV PATH="/venv/bin:$PATH"

# default envs (override as needed)
ENV LOG_LEVEL="INFO" \
    QUEUE_DIR="/queue" \
    STEMS_DIR="/stems" \
    CHUNKING_ENABLED="true" \
    CHUNK_LENGTH_MS="60000" \
    MIN_CHUNK_LENGTH_MS="30000" \
    CHUNK_MAX_ATTEMPTS="3" \
    MAX_RETRIES="3" \
    RETRY_DELAY="10" \
    SPLITTER_TYPE="SPLEETER" \
    STEMS="2" \
    STEM_TYPE="accompaniment"

EXPOSE 5000

ENTRYPOINT ["python", "splitter.py"]
