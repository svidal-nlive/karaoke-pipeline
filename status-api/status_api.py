# status_api.py
import os
import logging
import time
import requests
import shutil
from flask import Flask, jsonify, request, Response, abort, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from karaoke_shared.pipeline_utils import (
    redis_client,
    get_files_by_status,
    get_file_status,
    set_file_status,
    notify_all,
)

# Logging configuration
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

# Directories from env
DIRS = {
    "input": os.environ.get("INPUT_DIR", "/input"),
    "queue": os.environ.get("QUEUE_DIR", "/queue"),
    "metadata_extracted": os.environ.get("META_DIR", "/metadata"),
    "split": os.environ.get("STEMS_DIR", "/stems"),
    "packaged": os.environ.get("OUTPUT_DIR", "/output"),
    "organized": os.environ.get("ORG_DIR", "/organized"),
    "error":  os.environ.get("QUEUE_DIR", "/queue"),
}

# Flask + CORS
app = Flask(__name__)
# Replace with your actual dashboard URL
DASHBOARD_ORIGIN = os.environ.get("DASHBOARD_ORIGIN", "https://kdash.vectorhost.net")
CORS(app, origins=[DASHBOARD_ORIGIN], expose_headers=["Content-Range"])

# --- Upload endpoint remains the same ---
@app.route('/input', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        abort(400, 'No file part')
    file = request.files['file']
    if file.filename == '':
        abort(400, 'No selected file')
    filename = secure_filename(file.filename)
    dest = os.path.join(DIRS['input'], filename)
    file.save(dest)
    return jsonify({'status': 'success', 'filename': filename}), 201

# --- Health ---
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

# --- LIST ALL FILES ---
@app.route("/status")
def list_status():
    # gather all base names
    all_bases = set()
    for stage, path in DIRS.items():
        suf = {
            "input": ".mp3",
            "queue": ".ready",
            "metadata_extracted": ".json",
            "packaged": ".mp3",
            "organized": ".mp3",
            "split": "",
            "error": ".error",
        }[stage]
        if os.path.exists(path):
            for f in os.listdir(path):
                if f.endswith(suf):
                    all_bases.add(os.path.splitext(f)[0])
    statuses = [ get_file_status(f"{b}.mp3") for b in sorted(all_bases) ]

    # Build response as a plain array + Content-Range header
    total = len(statuses)
    resp = make_response(jsonify(statuses), 200)
    resp.headers["Content-Range"] = f"items 0-{total-1}/{total}"
    return resp

# --- GET ONE FILE STATUS ---
@app.route("/status/<filename>")
def status_single(filename):
    result = get_file_status(filename)
    if not result["stages"]:
        abort(404, f"File {filename} not found in pipeline")
    return jsonify(result)

# --- LIST ERROR FILES ---
@app.route("/error-files")
def list_error_files():
    errors = get_files_by_status("error")
    details = [ get_file_status(f) for f in errors ]
    total = len(details)
    resp = make_response(jsonify(details), 200)
    resp.headers["Content-Range"] = f"items 0-{total-1}/{total}"
    return resp

# --- RETRY ---
@app.route("/retry", methods=["POST"])
def retry_file():
    data = request.json or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    key = f"file:{filename}"
    if not redis_client.exists(key):
        return jsonify({"error": "File not found"}), 404

    set_file_status(filename, "queued")
    for stage in ["metadata", "splitter", "packager", "organizer"]:
        redis_client.delete(f"{stage}_retries:{filename}")
    redis_client.hdel(key, "error")
    notify_all("File Retry Triggered", f"🔄 File {filename} reset to queued.")
    return jsonify({"message": "ok"}), 200

# --- PIPELINE HEALTH ---
@app.route("/pipeline-health")
def pipeline_health():
    stages = ["queue", "metadata_extracted", "split", "packaged", "organized", "error"]
    return jsonify({ s: len(get_files_by_status(s)) for s in stages })

# --- ERROR DETAILS ---
@app.route("/error-details/<filename>")
def error_details(filename):
    err = redis_client.hget(f"file:{filename}", "error")
    if not err:
        return jsonify({"filename": filename, "error": "No error found."}), 404
    return jsonify({"filename": filename, "error": err})

@app.route("/metrics")
def metrics():
    stages = [
        "queued",
        "metadata_extracted",
        "split",
        "packaged",
        "organized",
        "error",
    ]
    metrics_lines = []
    for stage in stages:
        count = len(get_files_by_status(stage))
        metrics_lines.append(f"karaoke_files_{stage} {count}")
    uptime = int(time.time() - start_time)
    metrics_lines.append(f"karaoke_statusapi_uptime_seconds {uptime}")
    return Response("\n".join(metrics_lines), mimetype="text/plain")

@app.route("/reset", methods=["POST"])
def reset_pipeline():
    if (
        os.getenv("ENV") != "dev"
        and os.getenv("DEBUG", "false").lower() != "true"
    ):
        return (
            jsonify({"error": "Reset is only allowed in debug/dev mode"}),
            403,
        )
    full = request.args.get("full") == "true"
    cleared = []
    folders = [DIRS[k] for k in DIRS] + (['/logs'] if full else [])
    for folder in folders:
        if os.path.exists(folder):
            for entry in os.listdir(folder):
                path = os.path.join(folder, entry)
                try:
                    if os.path.isfile(path) or os.path.islink(path):
                        os.unlink(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                    cleared.append(path)
                except Exception as e:
                    logger.warning(f"Error cleaning {path}: {e}")
    for key in redis_client.scan_iter("file:*"):
        redis_client.delete(key)
    return jsonify({"status": "reset complete", "cleared": cleared}), 200

# Test asset endpoints

def fetch_test_asset():
    try:
        r = requests.get(TEST_ASSET_URL, timeout=30)
        r.raise_for_status()
        os.makedirs(os.path.dirname(TEST_ASSET_PATH), exist_ok=True)
        with open(TEST_ASSET_PATH, "wb") as f:
            f.write(r.content)
        logger.info(f"Test asset fetched and saved to {TEST_ASSET_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to fetch test asset: {e}")
        return False

@app.route("/inject-test-file", methods=["POST"])
def inject_test_file():
    if (
        os.getenv("ENV") != "dev"
        and os.getenv("DEBUG", "false").lower() != "true"
    ):
        return (
            jsonify(
                {"error": "Test injection only allowed in debug/dev mode"}
            ),
            403,
        )
    src = TEST_ASSET_PATH
    dest = os.path.join(DIRS["input"], "01-Chosen.mp3")
    if not os.path.exists(src):
        logger.info(f"Test file missing at {src}, attempting to fetch.")
        success = fetch_test_asset()
        if not success or not os.path.exists(src):
            return (
                jsonify(
                    {
                        "error": f"Test file could not be found or fetched at {src}"
                    }
                ),
                404,
            )
    try:
        shutil.copy2(src, dest)
        return jsonify({"status": "injected", "path": dest}), 200
    except Exception as e:
        logger.error(f"Injection failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
