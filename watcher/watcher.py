import time
import os
import shutil
import logging
import threading
from flask import Flask
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import traceback
import datetime

from karaoke_shared.pipeline_utils import (
    set_file_status,
    get_files_by_status,
    set_file_error,
    notify_all,
    clean_string,
    publish,
    STREAM_QUEUED,
)

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

        fname = os.path.basename(event.src_path)
        fname = clean_string(fname)

        # skip if already errored
        if fname in get_files_by_status("error"):
            logger.warning(f"File {fname} is in error state, skipping.")
            return

        try:
            # wait for file to stabilize
            stable_count = 0
            while True:
                if not os.path.exists(event.src_path):
                    return
                size0 = os.path.getsize(event.src_path)
                mtime0 = os.path.getmtime(event.src_path)
                time.sleep(2)
                if not os.path.exists(event.src_path):
                    return
                size1 = os.path.getsize(event.src_path)
                mtime1 = os.path.getmtime(event.src_path)

                if size0 == size1 and mtime0 == mtime1:
                    stable_count += 1
                else:
                    stable_count = 0

                if stable_count >= STABILITY_CHECKS:
                    break

            # copy into queue
            dest = os.path.join(QUEUE_DIR, fname)
            shutil.copy2(event.src_path, dest)

            # set status & publish
            set_file_status(fname, "queued")
            publish(STREAM_QUEUED, fname)

            logger.info(f"Queued {fname} and published to {STREAM_QUEUED}")

        except Exception as e:
            tb = traceback.format_exc()
            ts = datetime.datetime.now().isoformat()
            error_details = f"{ts}\nException: {e}\n\n{tb}"
            set_file_error(fname, error_details)
            notify_all(
                "Karaoke Pipeline Error",
                f"Error in watcher for {fname} at {ts}:\n{e}",
            )


def initial_scan_and_queue():
    """Queue any existing .mp3 files in INPUT_DIR at startup."""
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith(".mp3"):
            continue
        clean_name = clean_string(fname)
        src = os.path.join(INPUT_DIR, fname)
        dest = os.path.join(QUEUE_DIR, clean_name)
        if os.path.exists(dest):
            continue
        try:
            shutil.copy2(src, dest)
            set_file_status(clean_name, "queued")
            publish(STREAM_QUEUED, clean_name)
            logger.info(f"Initial scan: queued {clean_name} and published to {STREAM_QUEUED}")
        except Exception as e:
            logger.error(f"Failed to queue {clean_name} on initial scan: {e}")


def run_watcher():
    os.makedirs(QUEUE_DIR, exist_ok=True)
    initial_scan_and_queue()

    event_handler = MP3Handler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=True)
    observer.start()
    logger.info("Watcher started and listening for new .mp3 files.")

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
