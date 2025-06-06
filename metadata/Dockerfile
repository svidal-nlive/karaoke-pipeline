# syntax=docker/dockerfile:1

FROM python:3.12-slim AS build

# Setup non-root user
ARG PUID=1000
ARG PGID=1000

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install pip dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY . .

# Add non-root user for runtime
RUN groupadd -g ${PGID} appuser && \
    useradd -u ${PUID} -g ${PGID} -m appuser

USER ${PUID}:${PGID}
WORKDIR /app

ENV PYTHONUNBUFFERED=1

CMD ["python", "metadata.py"]
