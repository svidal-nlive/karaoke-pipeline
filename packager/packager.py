import os
import logging
import time
import subprocess
import shutil
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
}
logging.basicConfig(
    level=LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {LOG_LEVEL} level")

STEMS_DIR = os.environ.get("STEMS_DIR", "/stems")
PACKAGED_DIR = os.environ.get("PACKAGED_DIR", "/packaged")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 10))
PACKAGE_FORMAT = os.environ.get("PACKAGE_FORMAT", "zip")  # or tar

def package_stems(song_name):
    stems_path = os.path.join(STEMS_DIR, clean_string(song_name))
    if not os.path.exists(stems_path):
        raise FileNotFoundError(f"Stems directory not found: {stems_path}")

    output_dir = os.path.join(PACKAGED_DIR, clean_string(song_name))
    os.makedirs(output_dir, exist_ok=True)

    # Zip up all the stem files
    archive_base = os.path.join(PACKAGED_DIR, clean_string(song_name))
    if PACKAGE_FORMAT == "zip":
        archive_path = shutil.make_archive(archive_base, "zip", stems_path)
    elif PACKAGE_FORMAT == "tar":
        archive_path = shutil.make_archive(archive_base, "gztar", stems_path)
    else:
        raise ValueError("Unknown PACKAGE_FORMAT")
    return archive_path

def process_file(song_name):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            archive_path = package_stems(song_name)
            logger.info(f"Packaged stems for {song_name} at {archive_path}")
            return True
        except Exception as e:
            logger.error(f"Error in packaging (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return str(e)

def main():
    while True:
        files = get_files_by_status("split")
        for file in files:
            song_name = os.path.splitext(file)[0]

            def process_func():
                result = process_file(song_name)
                if result is True:
                    set_file_status(file, "packaged")
                    redis_client.delete(f"packager_retries:{file}")
                    notify_all(
                        "Karaoke Pipeline Success",
                        f"✅ Packaging completed for {file}",
                    )
                else:
                    raise Exception(result)
                return True

            try:
                handle_auto_retry(
                    "packager",
                    file,
                    func=process_func,
                    max_retries=MAX_RETRIES,
                    retry_delay=RETRY_DELAY,
                )
            except Exception as e:
                tb = traceback.format_exc()
                timestamp = datetime.datetime.now().isoformat()
                error_details = (
                    f"{timestamp}\nPackager error: {e}\n\nTraceback:\n{tb}"
                )
                set_file_error(file, error_details)
                notify_all(
                    "Karaoke Pipeline Error",
                    f"❌ Packaging failed for {file}: {e}",
                )
                redis_client.incr(f"packager_retries:{file}")
        time.sleep(5)

if __name__ == "__main__":
    main()
