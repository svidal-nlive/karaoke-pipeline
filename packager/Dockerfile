# packager/Dockerfile
FROM python:3.11-slim

ARG PUID=1001
ARG PGID=1001

ENV PUID=${PUID}
ENV PGID=${PGID}
ENV PYTHONUNBUFFERED=1

RUN groupadd -g ${PGID} appuser && useradd -u ${PUID} -g appuser -m appuser

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY packager/requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY shared /app/shared
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

COPY packager/karaoke_packager.py /app/karaoke_packager.py

RUN chown -R ${PUID}:${PGID} /app

USER ${PUID}:${PGID}

CMD ["python", "karaoke_packager.py"]
