import os
import json
import time
import logging
import requests
import shutil
from flask import Flask, jsonify, request, Response, abort, make_response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pipeline_utils.pipeline_utils import (
    redis_client,
    get_files_by_status,
    get_file_status,
    set_file_status,
    notify_all,
    STREAM_QUEUED,
    STREAM_METADATA_DONE,
    STREAM_SPLIT_DONE,
    STREAM_PACKAGED,
    STREAM_ORGANIZED,
)

# ————— Logging —————
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}
logging.basicConfig(level=LEVELS[LOG_LEVEL], format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {LOG_LEVEL}")

# ————— Flask + CORS —————
app = Flask(__name__)
DASHBOARD_ORIGIN = os.environ.get("DASHBOARD_ORIGIN", "https://mydash.vectorhost.net")
CORS(app, origins=[DASHBOARD_ORIGIN], expose_headers=["Content-Range"])

# ————— Upload —————
INPUT = os.environ.get("INPUT_DIR", "/input")
@app.route('/input', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        abort(400, 'No file part')
    f = request.files['file']
    if not f.filename:
        abort(400, 'No selected file')
    fn = secure_filename(f.filename)
    f.save(os.path.join(INPUT, fn))
    return jsonify({'status':'success','filename':fn}), 201

# ————— REST endpoints —————
@app.route("/status")
def list_status():
    all_bases = set()
    suffixes = {
        "input": ".mp3","queued": ".ready","metadata_extracted": ".json",
        "split": "","packaged": ".zip","organized": ".mp3","error": ".error",
    }
    for stage, suf in suffixes.items():
        path = {
            "input": os.environ.get("INPUT_DIR","/input"),
            "queued": os.environ.get("QUEUE_DIR","/queue"),
            "metadata_extracted": os.environ.get("META_DIR","/metadata"),
            "split": os.environ.get("STEMS_DIR","/stems"),
            "packaged": os.environ.get("OUTPUT_DIR","/output"),
            "organized": os.environ.get("ORG_DIR","/organized"),
            "error": os.environ.get("QUEUE_DIR","/queue"),
        }[stage]
        if os.path.exists(path):
            for f in os.listdir(path):
                if f.endswith(suf):
                    all_bases.add(os.path.splitext(f)[0])
    statuses = [get_file_status(f"{b}.mp3") for b in sorted(all_bases)]
    total = len(statuses)
    resp = make_response(jsonify(statuses), 200)
    resp.headers["Content-Range"] = f"items 0-{total-1}/{total}"
    return resp

@app.route("/error-files")
def list_error_files():
    errs = get_files_by_status("error")
    details = [get_file_status(f) for f in errs]
    total = len(details)
    resp = make_response(jsonify(details), 200)
    resp.headers["Content-Range"] = f"items 0-{total-1}/{total}"
    return resp

@app.route("/status/<filename>")
def status_single(filename):
    result = get_file_status(filename)
    if not result["status"] or result["status"]=="unknown":
        abort(404, f"{filename} not found")
    return jsonify(result)

@app.route("/retry", methods=["POST"])
def retry_file():
    data = request.json or {}
    fn = data.get("filename")
    if not fn:
        return jsonify({"error":"No filename provided"}),400
    key = f"file:{fn}"
    if not redis_client.exists(key):
        return jsonify({"error":"File not found"}),404
    set_file_status(fn,"queued")
    for stage in ["metadata","splitter","packager","organizer"]:
        redis_client.delete(f"{stage}_retries:{fn}")
    redis_client.hdel(key,"error")
    notify_all("File Retry","🔄 Reset to queued: "+fn)
    return jsonify({"message":"ok"}),200

@app.route("/pipeline-health")
def pipeline_health():
    stages = ["queued","metadata_extracted","split","packaged","organized","error"]
    counts = {s: len(get_files_by_status(s)) for s in stages}
    return jsonify(counts)

# ————— SSE stream for real-time updates —————
@app.route("/stream")
def stream():
    streams = [STREAM_QUEUED, STREAM_METADATA_DONE, STREAM_SPLIT_DONE, STREAM_PACKAGED, STREAM_ORGANIZED]
    last_ids = {s: "0-0" for s in streams}

    def event_gen():
        while True:
            streams_dict = {s: last_ids[s] for s in streams}
            resp = redis_client.xread(
                streams=streams_dict,
                block=5000,
                count=10
            )
            if not resp:
                continue
            for stream_name, messages in resp:
                for msg_id, data in messages:
                    last_ids[stream_name] = msg_id
                    payload = json.dumps({"stream": stream_name, "file": data.get("file")})
                    yield f"event: {stream_name}\ndata: {payload}\n\n"
    return Response(stream_with_context(event_gen()), mimetype="text/event-stream")

# ————— Health —————
@app.route("/health")
def health():
    return jsonify({"status":"ok"}),200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("STATUS_API_PORT",5001)))
