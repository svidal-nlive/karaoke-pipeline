# syntax=docker/dockerfile:1

FROM python:3.12-slim AS build

ARG PUID=1000
ARG PGID=1000

# System dependencies for Spleeter and audio tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ffmpeg \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Setup non-root user
RUN groupadd -g ${PGID} appuser && \
    useradd -u ${PUID} -g ${PGID} -m appuser

USER ${PUID}:${PGID}
WORKDIR /app

ENV PYTHONUNBUFFERED=1

CMD ["python", "splitter.py"]
