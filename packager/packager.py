# packager/packager.py

import os
import logging
import json
import time
import threading
import traceback
from flask import Flask, jsonify
from pydub import AudioSegment
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from pipeline_utils.pipeline_utils import (
    redis_client,
    STREAM_SPLIT_DONE,
    STREAM_PACKAGED,
    set_file_status,
    set_file_error,
    notify_all,
    clean_string,
    handle_auto_retry,
)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LEVELS = {
    "DEBUG": logging.DEBUG, "INFO": logging.INFO,
    "WARNING": logging.WARNING, "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
logging.basicConfig(
    level=LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {LOG_LEVEL} level")

GROUP_NAME = os.environ.get("PACKAGER_GROUP", "packager-group")
CONSUMER_NAME = os.environ.get("PACKAGER_CONSUMER", "packager-consumer")

try:
    redis_client.xgroup_create(
        STREAM_SPLIT_DONE, GROUP_NAME, id="0", mkstream=True
    )
    logger.info(f"Created consumer group {GROUP_NAME} on {STREAM_SPLIT_DONE}")
except Exception:
    pass

STEMS_DIR = os.environ.get("STEMS_DIR", "/stems")
META_DIR = os.environ.get("META_DIR", "/metadata")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/output")
STEM_TYPE = [
    s.strip().lower() for s in os.environ.get("STEM_TYPE", "vocals,accompaniment").split(",") if s.strip()
]
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 10))

def robust_load_metadata(meta_path):
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def mix_selected_stems(stems_folder, stems_to_mix):
    final = None
    for stem in stems_to_mix:
        for ext in ["wav", "mp3", "flac"]:
            stem_file = os.path.join(stems_folder, f"{stem}.{ext}")
            if os.path.exists(stem_file):
                seg = AudioSegment.from_file(stem_file)
                final = seg if final is None else final.overlay(seg)
                break
    if final is None:
        raise RuntimeError("No stems found to mix.")
    return final

def apply_metadata(mp3_path, metadata):
    try:
        audio = MP3(mp3_path, ID3=EasyID3)
        field_map = {"TIT2": "title", "TPE1": "artist", "TALB": "album", "TRCK": "tracknumber"}
        for k, v in field_map.items():
            if k in metadata:
                audio[v] = str(metadata[k])
        audio.save()
    except Exception as e:
        logging.warning(f"Metadata tagging failed: {e}")

def process_packaging(song_name):
    stems_path = os.path.join(STEMS_DIR, clean_string(song_name))
    meta_path = os.path.join(META_DIR, f"{song_name}.mp3.json")
    output_mp3 = os.path.join(OUTPUT_DIR, f"{song_name}.mp3")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    meta = robust_load_metadata(meta_path)
    audio = mix_selected_stems(stems_path, STEM_TYPE)
    audio.export(output_mp3, format="mp3")
    apply_metadata(output_mp3, meta)
    return output_mp3

def run_packager():
    logger.info("Packager listening on Redis Stream...")
    while True:
        entries = redis_client.xreadgroup(
            GROUP_NAME, CONSUMER_NAME,
            {STREAM_SPLIT_DONE: ">"},
            count=1, block=5000
        )
        if not entries:
            continue

        for _stream, messages in entries:
            for msg_id, data in messages:
                filename = data.get("file")
                song = os.path.splitext(filename)[0]

                def _do_package():
                    path = process_packaging(song)
                    set_file_status(filename, "packaged")
                    redis_client.xadd(STREAM_PACKAGED, {"file": filename})
                    logger.info(f"Packaged and published: {filename}")
                    return True

                try:
                    handle_auto_retry(
                        "packager", filename, func=_do_package,
                        max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY,
                    )
                except Exception:
                    # Already logged
                    pass
                finally:
                    redis_client.xack(STREAM_SPLIT_DONE, GROUP_NAME, msg_id)

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    t = threading.Thread(target=run_packager, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PACKAGER_PORT", 5000)))
