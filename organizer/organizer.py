# organizer/organizer.py

import os
import shutil
import logging
import threading
import traceback
import datetime
from flask import Flask, jsonify
from karaoke_shared.pipeline_utils import (
    redis_client,
    STREAM_PACKAGED,
    STREAM_ORGANIZED,
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
GROUP_NAME    = os.environ.get("ORGANIZER_GROUP",    "organizer-group")
CONSUMER_NAME = os.environ.get("ORGANIZER_CONSUMER", "organizer-consumer")
# Ensure the consumer group exists
try:
    redis_client.xgroup_create(
        STREAM_PACKAGED, GROUP_NAME, id="0", mkstream=True
    )
    logger.info(f"Created consumer group {GROUP_NAME} on {STREAM_PACKAGED}")
except Exception:
    pass  # already exists

# ————— Env & retry settings —————
OUTPUT_DIR  = os.environ.get("OUTPUT_DIR",  "/output")
ORG_DIR     = os.environ.get("ORG_DIR",     "/organized")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 10))

# ————— Organizing logic —————
def organize_file(filename):
    # move or copy the packaged file into organized directory
    src = os.path.join(OUTPUT_DIR, clean_string(filename))
    if not os.path.exists(src):
        raise FileNotFoundError(f"Packaged file not found: {src}")

    os.makedirs(ORG_DIR, exist_ok=True)
    dest = os.path.join(ORG_DIR, clean_string(filename))
    shutil.copy2(src, dest)
    logger.info(f"Organized {filename} → {dest}")
    return True

# ————— Stream consumer loop —————
def run_organizer():
    logger.info("Organizer listening on Redis Stream...")
    while True:
        entries = redis_client.xreadgroup(
            GROUP_NAME, CONSUMER_NAME,
            {STREAM_PACKAGED: ">"},
            count=1, block=5000
        )
        if not entries:
            continue

        for _stream, messages in entries:
            for msg_id, data in messages:
                filename = data.get("file")

                def _do_organize():
                    result = organize_file(filename)
                    if result is True:
                        set_file_status(filename, "organized")
                        redis_client.xadd(STREAM_ORGANIZED, {"file": filename})
                        logger.info(f"Published organized: {filename}")
                        return True
                    raise Exception(result)

                try:
                    handle_auto_retry(
                        "organizer", filename,
                        func=_do_organize,
                        max_retries=MAX_RETRIES,
                        retry_delay=RETRY_DELAY,
                    )
                except Exception:
                    # final failure already logged / notified
                    pass
                finally:
                    # ack the message to avoid reprocessing
                    redis_client.xack(STREAM_PACKAGED, GROUP_NAME, msg_id)

# ————— Flask health endpoint —————
app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    t = threading.Thread(target=run_organizer, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("ORGANIZER_PORT", 5000)))
