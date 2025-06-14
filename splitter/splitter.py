# splitter/splitter.py

import os
import time
import logging
import tempfile
import subprocess
import traceback
from flask import Flask, jsonify
from pydub import AudioSegment
from pydub.utils import make_chunks
from karaoke_shared.pipeline_utils import (
    redis_client,
    STREAM_METADATA_EXTRACTED,
    STREAM_SPLIT,
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
    "HEALTH": logging.INFO,
}
logging.basicConfig(
    level=LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {LOG_LEVEL} level")

# ————— Stream / consumer config —————
GROUP_NAME    = os.environ.get("SPLITTER_GROUP",    "splitter-group")
CONSUMER_NAME = os.environ.get("SPLITTER_CONSUMER", "splitter-consumer")
# Ensure the group exists
try:
    redis_client.xgroup_create(
        STREAM_METADATA_EXTRACTED, GROUP_NAME, id="0", mkstream=True
    )
    logger.info(f"Created consumer group {GROUP_NAME} on {STREAM_METADATA_EXTRACTED}")
except Exception:
    pass  # group already exists

# ————— Env‐driven splitter settings —————
QUEUE_DIR           = os.environ.get("QUEUE_DIR", "/queue")
STEMS_DIR           = os.environ.get("STEMS_DIR", "/stems")
MAX_RETRIES         = int(os.environ.get("MAX_RETRIES",     3))
RETRY_DELAY         = int(os.environ.get("RETRY_DELAY",     10))
CHUNKING_ENABLED    = os.environ.get("CHUNKING_ENABLED", "false").lower() == "true"
CHUNK_LENGTH_MS     = int(os.environ.get("CHUNK_LENGTH_MS",      240000))
MIN_CHUNK_LENGTH_MS = int(os.environ.get("MIN_CHUNK_LENGTH_MS", str(CHUNK_LENGTH_MS // 2)))
CHUNK_MAX_ATTEMPTS  = int(os.environ.get("CHUNK_MAX_ATTEMPTS",  3))
SPLITTER_TYPE       = os.environ.get("SPLITTER_TYPE",     "SPLEETER").upper()
STEMS               = int(os.environ.get("STEMS",                2))
STEM_TYPE           = [
    s.strip().lower()
    for s in os.environ
        .get("STEM_TYPE", "vocals,accompaniment")
        .split(",")
    if s.strip()
]

logger.info(
    f"CHUNKING_ENABLED={CHUNKING_ENABLED}, "
    f"CHUNK_LENGTH_MS={CHUNK_LENGTH_MS}, MIN_CHUNK_LENGTH_MS={MIN_CHUNK_LENGTH_MS}, "
    f"CHUNK_MAX_ATTEMPTS={CHUNK_MAX_ATTEMPTS}"
)
logger.info(
    f"SPLITTER_TYPE={SPLITTER_TYPE}, STEMS={STEMS}, STEM_TYPE={STEM_TYPE}"
)

# ————— Model definitions —————
SPLEETER_MODELS = {
    2: ["vocals", "accompaniment"],
    4: ["vocals", "drums", "bass", "other"],
    5: ["vocals", "drums", "bass", "piano", "other"],
}
DEMUCS_MODELS = {
    2: ["vocals", "accompaniment"],
    4: ["vocals", "drums", "bass", "other"],
    6: ["vocals", "drums", "bass", "guitar", "piano", "other"],
}

def map_demucs_stem_name(stem, stems_num):
    mapping = {
        2: {"vocals": "vocals", "accompaniment": "no_vocals"},
        4: {"vocals": "vocals", "drums": "drums", "bass": "bass", "other": "other"},
        6: {"vocals": "vocals", "drums": "drums", "bass": "bass", "guitar": "guitar", "piano": "piano", "other": "other"},
    }
    return mapping.get(stems_num, {}).get(stem, stem)

def get_supported_stems(splitter_type, stems_num):
    if splitter_type == "SPLEETER":
        return SPLEETER_MODELS.get(stems_num, [])
    elif splitter_type == "DEMUCS":
        return DEMUCS_MODELS.get(stems_num, [])
    return []

def get_demucs_model_name(stems_num):
    if stems_num == 2:
        return "htdemucs"
    elif stems_num == 4:
        return "demucs"
    else:
        return "htdemucs"

# ————— Subprocess runners —————
def run_spleeter(input_path, output_dir, stems_num):
    model = f"spleeter:{stems_num}stems"
    logger.info(f"Running Spleeter: spleeter separate -p {model} -o {output_dir} {input_path}")
    result = subprocess.run(
        ["spleeter", "separate", "-p", model, "-o", output_dir, input_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    logger.info(f"Spleeter STDOUT:\n{result.stdout}")
    logger.info(f"Spleeter STDERR:\n{result.stderr}")
    if result.returncode != 0:
        raise RuntimeError(f"Spleeter error: {result.stderr}")
    return os.path.join(output_dir, os.path.splitext(os.path.basename(input_path))[0])

def run_demucs(input_path, output_dir, stems_num):
    model_name = get_demucs_model_name(stems_num)
    args = ["demucs", "-o", output_dir, "-n", model_name, input_path]
    if stems_num == 2:
        args += ["--two-stems", "vocals"]
    logger.info(f"Running Demucs: {' '.join(args)}")
    result = subprocess.run(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    logger.info(f"Demucs STDOUT:\n{result.stdout}")
    logger.info(f"Demucs STDERR:\n{result.stderr}")
    if result.returncode != 0:
        raise RuntimeError(f"Demucs error: {result.stderr}")
    # locate output folder
    model_dir = os.path.join(output_dir, model_name)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    candidate = os.path.join(model_dir, base_name)
    if os.path.isdir(candidate):
        return candidate
    for d in os.listdir(model_dir):
        dpath = os.path.join(model_dir, d)
        if os.path.isdir(dpath):
            return dpath
    raise RuntimeError("Demucs output folder not found.")

def filter_and_export_stems(stems_folder, keep_stems, dest_dir, splitter_type, stems_num):
    os.makedirs(dest_dir, exist_ok=True)
    exported = []
    for stem in keep_stems:
        out_stem = map_demucs_stem_name(stem, stems_num) if splitter_type == "DEMUCS" else stem
        for ext in ["wav", "mp3", "flac"]:
            src = os.path.join(stems_folder, f"{out_stem}.{ext}")
            if os.path.exists(src):
                AudioSegment.from_file(src).export(
                    os.path.join(dest_dir, f"{stem}.{ext}"), format=ext
                )
                exported.append(stem)
                break
    return exported

# ————— Core split logic with dynamic chunk‐fallback —————
def process_file(file_path, song_name):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # single‐pass
            if not CHUNKING_ENABLED:
                logger.info("Chunking disabled; full‐track split")
                out_dir = os.path.join(STEMS_DIR, song_name)
                os.makedirs(out_dir, exist_ok=True)
                stem_src = (
                    run_spleeter(file_path, out_dir, STEMS)
                    if SPLITTER_TYPE=="SPLEETER"
                    else run_demucs(file_path, out_dir, STEMS)
                )
                supported = get_supported_stems(SPLITTER_TYPE, STEMS)
                keep = [s for s in STEM_TYPE if s in supported] or supported
                exported = filter_and_export_stems(
                    stem_src, keep, out_dir, SPLITTER_TYPE, STEMS
                )
                logger.info(f"Exported stems: {exported}")
                return True

            # chunk‐mode with fallback
            logger.info(f"Chunking enabled; start length {CHUNK_LENGTH_MS}ms")
            audio = AudioSegment.from_file(file_path)
            chunk_length = CHUNK_LENGTH_MS

            for split_try in range(1, CHUNK_MAX_ATTEMPTS + 1):
                logger.info(f"Chunk attempt {split_try}/{CHUNK_MAX_ATTEMPTS} at {chunk_length}ms")
                try:
                    chunks = make_chunks(audio, chunk_length)
                    merged = {s: AudioSegment.empty() for s in STEM_TYPE}
                    with tempfile.TemporaryDirectory() as td:
                        for idx, chunk in enumerate(chunks):
                            cp = os.path.join(td, f"chunk_{idx}.mp3")
                            chunk.export(cp, format="mp3")
                            od = os.path.join(td, f"out_{idx}")
                            os.makedirs(od, exist_ok=True)
                            stem_src = (
                                run_spleeter(cp, od, STEMS)
                                if SPLITTER_TYPE=="SPLEETER"
                                else run_demucs(cp, od, STEMS)
                            )
                            supported = get_supported_stems(SPLITTER_TYPE, STEMS)
                            keep = [s for s in STEM_TYPE if s in supported] or supported
                            for s in keep:
                                fname = map_demucs_stem_name(s, STEMS) if SPLITTER_TYPE=="DEMUCS" else s
                                for ext in ["wav","mp3","flac"]:
                                    sf = os.path.join(stem_src, f"{fname}.{ext}")
                                    if os.path.exists(sf):
                                        seg = AudioSegment.from_file(sf)
                                        merged[s] += seg
                                        break
                        final_dir = os.path.join(STEMS_DIR, song_name)
                        os.makedirs(final_dir, exist_ok=True)
                        for s, seg in merged.items():
                            if len(seg)>0:
                                seg.export(os.path.join(final_dir, f"{s}.wav"), format="wav")
                        logger.info(f"Chunked stems exported to {final_dir}")
                    return True

                except Exception as e:
                    logger.error(f"Chunk error {split_try}: {e}")
                    if split_try < CHUNK_MAX_ATTEMPTS:
                        new_len = max(MIN_CHUNK_LENGTH_MS, chunk_length // 2)
                        if new_len < chunk_length:
                            logger.info(f"Reducing chunk length {chunk_length}→{new_len}")
                            chunk_length = new_len
                        else:
                            logger.warning("At minimum chunk size; retrying same size")
                        continue
                    raise

        except Exception as e:
            logger.error(f"Splitter attempt {attempt} failed: {e}\n{traceback.format_exc()}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return str(e)

# ————— Stream consumer loop —————
def run_splitter():
    logger.info("Splitter service listening on Redis Stream...")
    while True:
        entries = redis_client.xreadgroup(
            GROUP_NAME, CONSUMER_NAME,
            {STREAM_METADATA_EXTRACTED: ">"},
            count=1, block=5000
        )
        if not entries:
            continue

        for _stream, messages in entries:
            for msg_id, data in messages:
                filename = data.get("file")
                path = os.path.join(QUEUE_DIR, clean_string(filename))
                song = os.path.splitext(filename)[0]

                def _split():
                    result = process_file(path, song)
                    if result is True:
                        set_file_status(filename, "split")
                        redis_client.xadd(STREAM_SPLIT, {"file": filename})
                        logger.info(f"Split succeeded for {filename}")
                        return True
                    raise Exception(result)

                try:
                    handle_auto_retry(
                        "splitter", filename, func=_split,
                        max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY,
                    )
                except Exception:
                    # final failure already notified inside handle_auto_retry
                    pass
                finally:
                    redis_client.xack(
                        STREAM_METADATA_EXTRACTED, GROUP_NAME, msg_id
                    )

# ————— Flask health endpoint —————
app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=run_splitter, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("STATUS_API_PORT", 5000)))
