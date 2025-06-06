# metadata/Dockerfile
FROM python:3.11-slim

ARG PUID=1001
ARG PGID=1001

ENV PUID=${PUID}
ENV PGID=${PGID}
ENV PYTHONUNBUFFERED=1

RUN groupadd -g ${PGID} appuser && useradd -u ${PUID} -g appuser -m appuser

WORKDIR /app

COPY metadata/requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY shared /app/shared
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

COPY metadata/metadata_extractor.py /app/metadata_extractor.py

RUN chown -R ${PUID}:${PGID} /app

RUN mkdir -p /metadata/json && chown -R ${PUID}:${PGID} /metadata

USER ${PUID}:${PGID}

CMD ["python", "metadata_extractor.py"]
