# syntax=docker/dockerfile:1

FROM python:3.11-slim AS build

# No build dependencies for this service
WORKDIR /app

# Production image
FROM python:3.11-slim

COPY volume-init.py /app/volume-init.py

WORKDIR /app

# Make sure it is executable
RUN chmod +x volume-init.py

ENTRYPOINT ["python", "volume-init.py"]

