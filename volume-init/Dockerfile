FROM python:3.12-alpine

ARG PUID=1000
ARG PGID=1000

RUN addgroup -g ${PGID} appgroup && adduser -D -u ${PUID} -G appgroup appuser

WORKDIR /scripts

COPY volume-init.py .
RUN chmod +x volume-init.py

USER root

ENV PUID=${PUID}
ENV PGID=${PGID}

ENTRYPOINT ["python3", "/scripts/volume-init.py"]
