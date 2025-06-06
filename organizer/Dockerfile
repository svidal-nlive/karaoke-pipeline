# organizer/Dockerfile
FROM python:3.11-slim

ARG PUID=1001
ARG PGID=1001

ENV PUID=${PUID}
ENV PGID=${PGID}
ENV PYTHONUNBUFFERED=1

RUN groupadd -g ${PGID} appuser && useradd -u ${PUID} -g appuser -m appuser

WORKDIR /app

COPY organizer/requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY shared /app/shared
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

COPY organizer/organizer.py /app/organizer.py

RUN chown -R ${PUID}:${PGID} /app

USER ${PUID}:${PGID}

EXPOSE 5000
CMD ["python", "organizer.py"]
