FROM python:3.11-slim

RUN pip install watchdog

# beets must be available; if not on host, install here too
RUN pip install beets

COPY watcher.py /watcher.py

CMD ["python", "/watcher.py"]
