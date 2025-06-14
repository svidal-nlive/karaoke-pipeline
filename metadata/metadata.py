# metadata/metadata.py
import os
import json
import logging
import threading
import traceback
from flask import Flask, jsonify
from mutagen.mp3 import MP3
from karaoke_shared.pipeline_utils import (
    redis_client,
    STREAM_QUEUED,
    STREAM_METADATA_EXTRACTED,
    set_file_status,
    set_file_error,
    notify_all,
    clean_string,
    handle_auto_retry,
)

# ————— Logging setup —————
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LEVELS = {
    "DEBUG": logging.DEBUG, "INFO": logging.INFO,
    "WARNING": logging.WARNING, "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL, "HEALTH": logging.INFO,
}
logging.basicConfig(
    level=LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {LOG_LEVEL} level")

# ————— Redis Stream / consumer config —————
GROUP_NAME = os.environ.get("METADATA_GROUP", "metadata-group")
CONSUMER_NAME = os.environ.get("METADATA_CONSUMER", "metadata-consumer")

# make sure the queue stream & group exist
try:
    redis_client.xgroup_create(STREAM_QUEUED, GROUP_NAME, id="0", mkstream=True)
    logger.info(f"Created consumer group {GROUP_NAME} on {STREAM_QUEUED}")
except Exception:
    # group already exists
    pass

def extract_metadata(mp3_path):
    """Read ID3 tags via mutagen and return a dict."""
    audio = MP3(mp3_path)
    tags = audio.tags or {}
    return {
        "TIT2": clean_string(tags.get("TIT2", "Unknown Title")),
        "TPE1": clean_string(tags.get("TPE1", "Unknown Artist")),
        "TALB": clean_string(tags.get("TALB", "Unknown Album")),
        "TRCK": clean_string(tags.get("TRCK", "")),
    }

def run_extractor():
    logger.info("Metadata service listening on Redis Stream...")
    while True:
        # block until new entry arrives
        entries = redis_client.xreadgroup(
            GROUP_NAME, CONSUMER_NAME,
            { STREAM_QUEUED: ">" },
            count=1, block=5000  # ms
        )
        if not entries:
            continue

        for _stream, messages in entries:
            for msg_id, data in messages:
                filename = data.get("file")
                mp3_path = os.path.join(
                    os.environ.get("QUEUE_DIR", "/queue"),
                    clean_string(filename)
                )

                def _do_extract():
                    if not os.path.exists(mp3_path):
                        raise FileNotFoundError(mp3_path)
                    meta = extract_metadata(mp3_path)
                    meta_path = os.path.join(
                        os.environ.get("META_DIR", "/metadata"),
                        os.path.splitext(filename)[0] + ".mp3.json"
                    )
                    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(meta, f)
                    set_file_status(filename, "metadata_extracted")
                    logger.info(f"Extracted metadata for {filename}")

                try:
                    # retry on failures
                    handle_auto_retry(
                        "metadata", filename, func=_do_extract,
                        max_retries=int(os.environ.get("MAX_RETRIES", 3)),
                        retry_delay=int(os.environ.get("RETRY_DELAY", 5)),
                    )
                    # push downstream
                    redis_client.xadd(STREAM_METADATA_EXTRACTED, {"file": filename})
                except Exception as e:
                    # error already logged/notified by handle_auto_retry
                    pass
                finally:
                    # ack whether success or permanently failed
                    redis_client.xack(STREAM_QUEUED, GROUP_NAME, msg_id)

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    t = threading.Thread(target=run_extractor, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("STATUS_API_PORT", 5000)))
