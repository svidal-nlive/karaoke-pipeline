# packager/packager.py

import os
import time
import logging
import threading
import shutil
import traceback
from flask import Flask, jsonify
from karaoke_shared.pipeline_utils import (
    redis_client,
    STREAM_SPLIT,
    STREAM_PACKAGED,
    set_file_status,
    set_file_error,
    notify_all,
    clean_string,
    handle_auto_retry,
)

# ————— Logging setup —————
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
logging.basicConfig(
    level=LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {LOG_LEVEL} level")

# ————— Stream / consumer config —————
GROUP_NAME    = os.environ.get("PACKAGER_GROUP",    "packager-group")
CONSUMER_NAME = os.environ.get("PACKAGER_CONSUMER", "packager-consumer")
# Ensure the consumer group exists
try:
    redis_client.xgroup_create(
        STREAM_SPLIT, GROUP_NAME, id="0", mkstream=True
    )
    logger.info(f"Created consumer group {GROUP_NAME} on {STREAM_SPLIT}")
except Exception:
    pass  # group already exists

# ————— Env & retry settings —————
STEMS_DIR     = os.environ.get("STEMS_DIR",    "/stems")
OUTPUT_DIR    = os.environ.get("OUTPUT_DIR",   "/output")
MAX_RETRIES   = int(os.environ.get("MAX_RETRIES",    3))
RETRY_DELAY   = int(os.environ.get("RETRY_DELAY",   10))
PACKAGE_FORMAT = os.environ.get("PACKAGE_FORMAT", "zip")  # or "tar"

# ————— Packaging logic —————
def package_stems(song_name):
    stems_path = os.path.join(STEMS_DIR, clean_string(song_name))
    if not os.path.isdir(stems_path):
        raise FileNotFoundError(f"Stems dir missing: {stems_path}")

    base = clean_string(song_name)
    archive_base = os.path.join(OUTPUT_DIR, base)
    # ensure output dir
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if PACKAGE_FORMAT == "zip":
        archive_path = shutil.make_archive(archive_base, "zip", stems_path)
    elif PACKAGE_FORMAT == "tar":
        archive_path = shutil.make_archive(archive_base, "gztar", stems_path)
    else:
        raise ValueError(f"Unknown PACKAGE_FORMAT: {PACKAGE_FORMAT}")

    return archive_path

def process_packaging(song_name):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            path = package_stems(song_name)
            logger.info(f"Packaged {song_name} → {path}")
            return True
        except Exception as e:
            logger.error(f"Packaging error (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return str(e)

# ————— Stream consumer loop —————
def run_packager():
    logger.info("Packager listening on Redis Stream...")
    while True:
        entries = redis_client.xreadgroup(
            GROUP_NAME, CONSUMER_NAME,
            {STREAM_SPLIT: ">"},
            count=1, block=5000
        )
        if not entries:
            continue

        for _stream, messages in entries:
            for msg_id, data in messages:
                filename = data.get("file")
                song = os.path.splitext(filename)[0]

                def _do_package():
                    result = process_packaging(song)
                    if result is True:
                        # success
                        set_file_status(filename, "packaged")
                        redis_client.xadd(STREAM_PACKAGED, {"file": filename})
                        logger.info(f"Packaged and published: {filename}")
                        return True
                    raise Exception(result)

                try:
                    handle_auto_retry(
                        "packager", filename,
                        func=_do_package,
                        max_retries=MAX_RETRIES,
                        retry_delay=RETRY_DELAY,
                    )
                except Exception:
                    # final failure already handled by handle_auto_retry
                    pass
                finally:
                    # always ack to avoid replay
                    redis_client.xack(STREAM_SPLIT, GROUP_NAME, msg_id)

# ————— Flask health endpoint —————
app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    t = threading.Thread(target=run_packager, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PACKAGER_PORT", 5000)))
