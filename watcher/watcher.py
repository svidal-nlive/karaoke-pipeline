import time
import os
import shutil
import logging
import threading
from flask import Flask
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from karaoke_shared.pipeline_utils import (
    redis_client,
    STREAM_QUEUED,
    set_file_status,
    get_files_by_status,
    set_file_error,
    notify_all,
    clean_string,
)
import traceback
import datetime

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "HEALTH": logging.INFO,
}

logging.basicConfig(
    level=LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {LOG_LEVEL} level")

INPUT_DIR = os.environ.get("INPUT_DIR", "/input")
QUEUE_DIR = os.environ.get("QUEUE_DIR", "/queue")
STABILITY_CHECKS = int(os.environ.get("FILE_STABILITY_CHECKS", 4))

class MP3Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".mp3"):
            return
        fname = clean_string(os.path.basename(event.src_path))
        if fname in get_files_by_status("error"):
            logger.warning(f"File {fname} is in error state, skipping.")
            return
        try:
            stable_count = 0
            while True:
                if not os.path.exists(event.src_path):
                    return
                initial_size = os.path.getsize(event.src_path)
                initial_mtime = os.path.getmtime(event.src_path)
                time.sleep(2)
                if not os.path.exists(event.src_path):
                    return
                current_size = os.path.getsize(event.src_path)
                current_mtime = os.path.getmtime(event.src_path)
                if initial_size == current_size and initial_mtime == current_mtime:
                    stable_count += 1
                else:
                    stable_count = 0
                if stable_count >= STABILITY_CHECKS:
                    break

            dest = os.path.join(QUEUE_DIR, fname)
            shutil.copy2(event.src_path, dest)
            set_file_status(fname, "queued")
            # Publish to Redis Stream for the metadata service
            redis_client.xadd(STREAM_QUEUED, {"file": fname})
            logger.info(f"Queued {fname} and published to stream {STREAM_QUEUED}")

        except Exception as e:
            tb = traceback.format_exc()
            timestamp = datetime.datetime.now().isoformat()
            error_details = f"{timestamp}\nException: {e}\n\nTraceback:\n{tb}"
            set_file_error(fname, error_details)
            notify_all(
                "Karaoke Pipeline Error",
                f"Error in watcher for {fname} at {timestamp}:\n{e}",
            )

def initial_scan_and_queue():
    os.makedirs(QUEUE_DIR, exist_ok=True)
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith(".mp3"):
            continue
        src = os.path.join(INPUT_DIR, fname)
        dest = os.path.join(QUEUE_DIR, fname)
        if not os.path.exists(dest):
            try:
                shutil.copy2(src, dest)
                set_file_status(fname, "queued")
                redis_client.xadd(STREAM_QUEUED, {"file": fname})
                logger.info(f"Initial scan queued and streamed {fname}")
            except Exception as e:
                logger.error(f"Failed to queue {fname} on initial scan: {e}")

def run_watcher():
    initial_scan_and_queue()
    event_handler = MP3Handler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=True)
    observer.start()
    logger.info("Watcher started and listening for new MP3 files.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

app = Flask(__name__)

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    t = threading.Thread(target=run_watcher, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
