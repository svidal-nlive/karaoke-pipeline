# syntax=docker/dockerfile:1

FROM python:3.12-slim

ARG PUID=1000
ARG PGID=1000

# Install OS dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

COPY . .

RUN groupadd -g ${PGID} appuser && \
    useradd -u ${PUID} -g ${PGID} -m appuser

USER ${PUID}:${PGID}
WORKDIR /app

ENV PYTHONUNBUFFERED=1

CMD ["python", "organizer.py"]
