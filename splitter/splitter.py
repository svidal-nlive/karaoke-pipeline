# splitter/splitter.py
import os
import time
import logging
import tempfile
import subprocess
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

QUEUE_DIR = os.environ.get("QUEUE_DIR", "/queue")
STEMS_DIR = os.environ.get("STEMS_DIR", "/stems")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 10))

# --- New env config ---
CHUNKING_ENABLED = (
    os.environ.get("CHUNKING_ENABLED", "false").lower() == "true"
)
CHUNK_LENGTH_MS = int(os.environ.get("CHUNK_LENGTH_MS", 240000))
SPLITTER_TYPE = os.environ.get("SPLITTER_TYPE", "SPLEETER").upper()
STEMS = int(os.environ.get("STEMS", 2))
STEM_TYPE = [
    s.strip().lower()
    for s in os.environ.get("STEM_TYPE", "vocals,accompaniment").split(",")
    if s.strip()
]

logger.info(
    f"CHUNKING_ENABLED={CHUNKING_ENABLED} (raw env: {os.environ.get('CHUNKING_ENABLED')})"
)
logger.info(f"CHUNK_LENGTH_MS={CHUNK_LENGTH_MS}")
logger.info(f"SPLITTER_TYPE={SPLITTER_TYPE}")
logger.info(f"STEMS={STEMS}")
logger.info(f"STEM_TYPE={STEM_TYPE}")

# Model support dicts
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

# --- Stem mapping between user-friendly names and Demucs output files ---
def map_demucs_stem_name(stem, stems_num):
    mapping = {
        2: {"vocals": "vocals", "accompaniment": "no_vocals"},
        4: {
            "vocals": "vocals",
            "drums": "drums",
            "bass": "bass",
            "other": "other",
        },
        6: {
            "vocals": "vocals",
            "drums": "drums",
            "bass": "bass",
            "guitar": "guitar",
            "piano": "piano",
            "other": "other",
        },
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
        return "htdemucs"  # htdemucs supports 2-stem as of latest Demucs v4
    elif stems_num == 4:
        return "demucs"
    elif stems_num == 6:
        return "htdemucs"
    else:
        return "htdemucs"

def run_spleeter(input_path, output_dir, stems_num):
    model = f"spleeter:{stems_num}stems"
    logger.info(
        f"Running Spleeter: spleeter separate -p {model} -o {output_dir} {input_path}"
    )
    result = subprocess.run(
        [
            "spleeter",
            "separate",
            "-p",
            model,
            "-o",
            output_dir,
            input_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    logger.info(f"Spleeter STDOUT:\n{result.stdout}")
    logger.info(f"Spleeter STDERR:\n{result.stderr}")
    if result.returncode != 0:
        raise RuntimeError(f"Spleeter error: {result.stderr}")
    # Spleeter always writes stems under output_dir/song_name
    return os.path.join(
        output_dir, os.path.splitext(os.path.basename(input_path))[0]
    )

def run_demucs(input_path, output_dir, stems_num):
    model_name = get_demucs_model_name(stems_num)
    args = ["demucs", "-o", output_dir, "-n", model_name, input_path]
    if stems_num == 2:
        args += ["--two-stems", "vocals"]
    logger.info(f"Running Demucs: {' '.join(args)}")
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    logger.info(f"Demucs STDOUT:\n{result.stdout}")
    logger.info(f"Demucs STDERR:\n{result.stderr}")
    if result.returncode != 0:
        raise RuntimeError(f"Demucs error: {result.stderr}")
    # Output: output_dir/model_name/song_name
    model_dir = model_name
    out_path = os.path.join(
        output_dir,
        model_dir,
        os.path.splitext(os.path.basename(input_path))[0],
    )
    if not os.path.exists(out_path):
        # Sometimes Demucs uses just model name (without song subdir for short files)
        for d in os.listdir(os.path.join(output_dir, model_dir)):
            candidate = os.path.join(output_dir, model_dir, d)
            if os.path.isdir(candidate):
                out_path = candidate
                break
    if not os.path.exists(out_path):
        raise RuntimeError("Demucs output folder not found.")
    return out_path

def filter_and_export_stems(
    stems_folder, keep_stems, dest_dir, splitter_type="SPLEETER", stems_num=2
):
    os.makedirs(dest_dir, exist_ok=True)
    exported = []
    for stem in keep_stems:
        # Map Demucs names if necessary
        out_stem = stem
        if splitter_type == "DEMUCS":
            out_stem = map_demucs_stem_name(stem, stems_num)
        for ext in ["wav", "mp3", "flac"]:
            stem_file = os.path.join(stems_folder, f"{out_stem}.{ext}")
            if os.path.exists(stem_file):
                # Export as requested stem name for consistency
                AudioSegment.from_file(stem_file).export(
                    os.path.join(dest_dir, f"{stem}.{ext}"), format=ext
                )
                exported.append(stem)
                break
    return exported

def process_file(file_path, song_name):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # --- CHUNKING DISABLED: process full file
            if not CHUNKING_ENABLED:
                logger.info("Chunking is disabled; processing full track.")
                out_dir = os.path.join(STEMS_DIR, song_name)
                os.makedirs(out_dir, exist_ok=True)
                if SPLITTER_TYPE == "SPLEETER":
                    stem_dir = run_spleeter(file_path, out_dir, STEMS)
                elif SPLITTER_TYPE == "DEMUCS":
                    stem_dir = run_demucs(file_path, out_dir, STEMS)
                else:
                    raise RuntimeError(
                        f"Unknown SPLITTER_TYPE: {SPLITTER_TYPE}"
                    )

                supported = get_supported_stems(SPLITTER_TYPE, STEMS)
                keep = [s for s in STEM_TYPE if s in supported]
                if not keep:
                    logger.warning("No requested stems found in model! Using all supported stems.")
                    keep = supported
                exported = filter_and_export_stems(
                    stem_dir,
                    keep,
                    out_dir,
                    splitter_type=SPLITTER_TYPE,
                    stems_num=STEMS,
                )
                logger.info(f"Exported stems: {exported}")
                return True
            else:
                # --- CHUNKING ENABLED: chunk, split, merge stems ---
                logger.info(
                    f"Chunking is enabled (length: {CHUNK_LENGTH_MS} ms)"
                )
                audio = AudioSegment.from_file(file_path)
                chunks = make_chunks(audio, CHUNK_LENGTH_MS)
                temp_stem_data = {
                    stem: AudioSegment.empty() for stem in STEM_TYPE
                }
                with tempfile.TemporaryDirectory() as temp_dir:
                    for idx, chunk in enumerate(chunks):
                        chunk_path = os.path.join(temp_dir, f"chunk_{idx}.mp3")
                        chunk.export(chunk_path, format="mp3")
                        chunk_out = os.path.join(temp_dir, f"output_{idx}")
                        os.makedirs(chunk_out, exist_ok=True)
                        if SPLITTER_TYPE == "SPLEETER":
                            stem_dir = run_spleeter(
                                chunk_path, chunk_out, STEMS
                            )
                        elif SPLITTER_TYPE == "DEMUCS":
                            stem_dir = run_demucs(chunk_path, chunk_out, STEMS)
                        else:
                            raise RuntimeError(
                                f"Unknown SPLITTER_TYPE: {SPLITTER_TYPE}"
                            )
                        supported = get_supported_stems(SPLITTER_TYPE, STEMS)
                        keep = [s for s in STEM_TYPE if s in supported]
                        if not keep:
                            keep = supported
                        for stem in keep:
                            # Map Demucs names for chunked stems as well
                            out_stem = stem
                            if SPLITTER_TYPE == "DEMUCS":
                                out_stem = map_demucs_stem_name(stem, STEMS)
                            for ext in ["wav", "mp3", "flac"]:
                                stem_file = os.path.join(
                                    stem_dir, f"{out_stem}.{ext}"
                                )
                                if os.path.exists(stem_file):
                                    seg = AudioSegment.from_file(stem_file)
                                    temp_stem_data.setdefault(
                                        stem, AudioSegment.empty()
                                    )
                                    temp_stem_data[stem] += seg
                                    break
                    out_dir = os.path.join(STEMS_DIR, song_name)
                    os.makedirs(out_dir, exist_ok=True)
                    for stem, seg in temp_stem_data.items():
                        if len(seg) > 0:
                            seg.export(
                                os.path.join(out_dir, f"{stem}.wav"),
                                format="wav",
                            )
                    logger.info("Chunked stems exported to %s", out_dir)
                return True
        except Exception as e:
            logger.error(f"Error in splitter (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return str(e)

def main():
    while True:
        files = get_files_by_status("metadata_extracted")
        for file in files:
            file_path = os.path.join(QUEUE_DIR, clean_string(file))
            song_name = os.path.splitext(file)[0]
            if not os.path.exists(file_path):
                set_file_error(file, "File not found for splitting")
                continue

            def process_func():
                result = process_file(file_path, clean_string(song_name))
                if result is True:
                    set_file_status(file, "split")
                    redis_client.delete(f"splitter_retries:{file}")
                    notify_all(
                        "Karaoke Pipeline Success",
                        f"✅ Split completed for {file}",
                    )
                else:
                    raise Exception(result)
                return True

            try:
                handle_auto_retry(
                    "splitter",
                    file,
                    func=process_func,
                    max_retries=MAX_RETRIES,
                    retry_delay=RETRY_DELAY,
                )
            except Exception as e:
                tb = traceback.format_exc()
                timestamp = datetime.datetime.now().isoformat()
                error_details = (
                    f"{timestamp}\nSplitter error: {e}\n\nTraceback:\n{tb}"
                )
                set_file_error(file, error_details)
                notify_all(
                    "Karaoke Pipeline Error",
                    f"❌ Splitter failed for {file}: {e}",
                )
                redis_client.incr(f"splitter_retries:{file}")
        time.sleep(5)

if __name__ == "__main__":
    main()
