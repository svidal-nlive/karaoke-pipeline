# splitter/splitter.py

import os
import time
import logging
import tempfile
import subprocess
import traceback
from pydub import AudioSegment
from pydub.utils import make_chunks
from karaoke_shared.pipeline_utils import (
    set_file_status,
    get_files_by_status,
    set_file_error,
    notify_all,
    clean_string,
    redis_client,
    handle_auto_retry,
)

# --- Logging setup ---
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

# --- Pipeline dirs & retry config ---
QUEUE_DIR      = os.environ.get("QUEUE_DIR", "/queue")
STEMS_DIR      = os.environ.get("STEMS_DIR", "/stems")
MAX_RETRIES    = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY    = int(os.environ.get("RETRY_DELAY", 10))

# --- Chunking & splitter model config ---
CHUNKING_ENABLED      = os.environ.get("CHUNKING_ENABLED", "false").lower() == "true"
CHUNK_LENGTH_MS       = int(os.environ.get("CHUNK_LENGTH_MS", 240000))
MIN_CHUNK_LENGTH_MS   = int(os.environ.get("MIN_CHUNK_LENGTH_MS", str(CHUNK_LENGTH_MS // 2)))
CHUNK_MAX_ATTEMPTS    = int(os.environ.get("CHUNK_MAX_ATTEMPTS", 3))

SPLITTER_TYPE = os.environ.get("SPLITTER_TYPE", "SPLEETER").upper()
STEMS         = int(os.environ.get("STEMS", 2))
STEM_TYPE     = [
    s.strip().lower()
    for s in os.environ.get("STEM_TYPE", "vocals,accompaniment").split(",")
    if s.strip()
]

logger.info(f"CHUNKING_ENABLED={CHUNKING_ENABLED}")
logger.info(f"CHUNK_LENGTH_MS={CHUNK_LENGTH_MS}, MIN_CHUNK_LENGTH_MS={MIN_CHUNK_LENGTH_MS}, CHUNK_MAX_ATTEMPTS={CHUNK_MAX_ATTEMPTS}")
logger.info(f"SPLITTER_TYPE={SPLITTER_TYPE}, STEMS={STEMS}, STEM_TYPE={STEM_TYPE}")

# --- Model stem definitions ---
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

# --- Subprocess runners ---
def run_spleeter(input_path, output_dir, stems_num):
    model = f"spleeter:{stems_num}stems"
    logger.info(f"Running Spleeter: spleeter separate -p {model} -o {output_dir} {input_path}")
    result = subprocess.run(
        ["spleeter", "separate", "-p", model, "-o", output_dir, input_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
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
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.info(f"Demucs STDOUT:\n{result.stdout}")
    logger.info(f"Demucs STDERR:\n{result.stderr}")
    if result.returncode != 0:
        raise RuntimeError(f"Demucs error: {result.stderr}")
    # find output folder
    model_dir = os.path.join(output_dir, model_name)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    candidate = os.path.join(model_dir, base_name)
    if os.path.isdir(candidate):
        return candidate
    # fallback: pick any subdirectory under model_dir
    for d in os.listdir(model_dir):
        dpath = os.path.join(model_dir, d)
        if os.path.isdir(dpath):
            return dpath
    raise RuntimeError("Demucs output folder not found.")

def filter_and_export_stems(stems_folder, keep_stems, dest_dir, splitter_type, stems_num):
    os.makedirs(dest_dir, exist_ok=True)
    exported = []
    for stem in keep_stems:
        out_stem = stem
        if splitter_type == "DEMUCS":
            out_stem = map_demucs_stem_name(stem, stems_num)
        for ext in ["wav", "mp3", "flac"]:
            src = os.path.join(stems_folder, f"{out_stem}.{ext}")
            if os.path.exists(src):
                AudioSegment.from_file(src).export(
                    os.path.join(dest_dir, f"{stem}.{ext}"), format=ext
                )
                exported.append(stem)
                break
    return exported

# --- Core processing ---
def process_file(file_path, song_name):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # --- NO CHUNKING: single-pass split ---
            if not CHUNKING_ENABLED:
                logger.info("Chunking disabled; processing full track.")
                out_dir = os.path.join(STEMS_DIR, song_name)
                os.makedirs(out_dir, exist_ok=True)

                stem_folder = (
                    run_spleeter(file_path, out_dir, STEMS)
                    if SPLITTER_TYPE == "SPLEETER"
                    else run_demucs(file_path, out_dir, STEMS)
                )

                supported = get_supported_stems(SPLITTER_TYPE, STEMS)
                keep = [s for s in STEM_TYPE if s in supported] or supported
                exported = filter_and_export_stems(
                    stem_folder, keep, out_dir, SPLITTER_TYPE, STEMS
                )
                logger.info(f"Exported stems: {exported}")
                return True

            # --- WITH CHUNKING: dynamic chunk-size reduction on failures ---
            logger.info(f"Chunking enabled; initial length {CHUNK_LENGTH_MS} ms")
            audio = AudioSegment.from_file(file_path)
            chunk_length = CHUNK_LENGTH_MS

            for split_try in range(1, CHUNK_MAX_ATTEMPTS + 1):
                logger.info(f"Chunk‐split attempt {split_try}/{CHUNK_MAX_ATTEMPTS} using {chunk_length} ms chunks")
                try:
                    chunks = make_chunks(audio, chunk_length)
                    if not chunks:
                        raise RuntimeError("No chunks generated")
                    # prepare merger buffer
                    merged = {stem: AudioSegment.empty() for stem in STEM_TYPE}

                    with tempfile.TemporaryDirectory() as td:
                        for idx, chunk in enumerate(chunks):
                            cp = os.path.join(td, f"chunk_{idx}.mp3")
                            chunk.export(cp, format="mp3")
                            outd = os.path.join(td, f"out_{idx}")
                            os.makedirs(outd, exist_ok=True)

                            stem_src = (
                                run_spleeter(cp, outd, STEMS)
                                if SPLITTER_TYPE == "SPLEETER"
                                else run_demucs(cp, outd, STEMS)
                            )

                            supported = get_supported_stems(SPLITTER_TYPE, STEMS)
                            keep = [s for s in STEM_TYPE if s in supported] or supported

                            for stem in keep:
                                fname = stem
                                if SPLITTER_TYPE == "DEMUCS":
                                    fname = map_demucs_stem_name(stem, STEMS)
                                for ext in ["wav", "mp3", "flac"]:
                                    sf = os.path.join(stem_src, f"{fname}.{ext}")
                                    if os.path.exists(sf):
                                        seg = AudioSegment.from_file(sf)
                                        merged[stem] += seg
                                        break

                        # write merged
                        final_dir = os.path.join(STEMS_DIR, song_name)
                        os.makedirs(final_dir, exist_ok=True)
                        for stem, seg in merged.items():
                            if len(seg) > 0:
                                seg.export(os.path.join(final_dir, f"{stem}.wav"), format="wav")
                        logger.info(f"Chunked stems exported to {final_dir}")

                    # success—exit split loop
                    return True

                except Exception as split_err:
                    logger.error(f"Error in chunk‐split (attempt {split_try}): {split_err}")
                    # if more split attempts remain, shrink chunk size
                    if split_try < CHUNK_MAX_ATTEMPTS:
                        new_len = max(MIN_CHUNK_LENGTH_MS, chunk_length // 2)
                        if new_len < chunk_length:
                            logger.info(f"Reducing chunk size: {chunk_length} → {new_len}")
                            chunk_length = new_len
                        else:
                            logger.warning(f"At minimum chunk size ({chunk_length} ms), will retry same size")
                        continue
                    # no more split attempts: bubble up
                    raise

        except Exception as e:
            logger.error(f"Error in splitter (file‐level attempt {attempt}): {e}\n{traceback.format_exc()}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            # final failure
            return str(e)

def main():
    while True:
        files = get_files_by_status("metadata_extracted")
        for file in files:
            song = clean_string(os.path.splitext(file)[0])
            path = os.path.join(QUEUE_DIR, clean_string(file))
            if not os.path.exists(path):
                set_file_error(file, "File not found for splitting")
                continue

            def _proc():
                result = process_file(path, song)
                if result is True:
                    set_file_status(file, "split")
                    redis_client.delete(f"splitter_retries:{file}")
                    notify_all("Karaoke Pipeline Success", f"✅ Split completed for {file}")
                    return True
                else:
                    raise Exception(result)

            try:
                handle_auto_retry("splitter", file, func=_proc, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY)
            except Exception as e:
                set_file_error(file, f"Splitter completely failed: {e}")
                notify_all("Karaoke Pipeline Error", f"❌ Splitter failed for {file}: {e}")
                redis_client.incr(f"splitter_retries:{file}")

        time.sleep(5)

if __name__ == "__main__":
    main()
