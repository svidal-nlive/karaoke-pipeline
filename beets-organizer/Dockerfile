FROM python:3.11-slim

# Install system deps for beets and plugins
RUN apt-get update && \
    apt-get install -y \
      mp3gain ffmpeg python3-pip git \
    && rm -rf /var/lib/apt/lists/*

# Install beets and common plugins
RUN pip install beets flask flask_cors requests

# Set up config and library directories
ENV BEETSDIR=/config

WORKDIR /music

# Default CMD: run the web UI, allow interactive use!
CMD ["beet", "-c", "/config/config.yaml", "web"]
