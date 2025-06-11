import os
import time
import requests

# Use environment variable or default to status-api port
STATUS_API_URL = os.environ.get("STATUS_API_URL", "http://localhost:5001")

TEST_INPUT_DIR = os.path.join(os.getcwd(), "input")

def wait_for_status_api(timeout=60):
    """Wait for the status API /health endpoint to be healthy (accepts text or JSON)."""
    url = f"{STATUS_API_URL}/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                # Accept 'ok' string, {"status": "ok"} JSON, or any 200
                if r.headers.get("Content-Type", "").startswith("application/json"):
                    try:
                        j = r.json()
                        if j.get("status") == "ok":
                            return True
                    except Exception:
                        pass
                elif r.text.strip().lower() == "ok":
                    return True
                else:
                    # Any 200 counts as healthy, unless you want to be stricter
                    return True
        except Exception as ex:
            pass
        time.sleep(2)
    return False

def wait_for_file_status(filename, status, timeout=90):
    """Wait for a file to reach a specific pipeline status."""
    url = f"{STATUS_API_URL}/status"
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                files = r.json().get("files", [])
                for f in files:
                    if f["filename"] == filename and f["status"] == status:
                        return True
        except Exception:
            pass
        time.sleep(2)
    return False

def inject_mp3_from_url(url, filename):
    """Download a remote MP3 to input/ if not already present."""
    os.makedirs(TEST_INPUT_DIR, exist_ok=True)
    local_file = os.path.join(TEST_INPUT_DIR, filename)
    if not os.path.exists(local_file):
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        with open(local_file, "wb") as f:
            f.write(r.content)
    return local_file

def inject_corrupted_mp3(filename="corrupted.mp3"):
    """Create a corrupted MP3 file (truncated header)."""
    os.makedirs(TEST_INPUT_DIR, exist_ok=True)
    local_file = os.path.join(TEST_INPUT_DIR, filename)
    with open(local_file, "wb") as f:
        f.write(b"ID3\x04\x00\x00\x00\x00\x00\x21corruptdata")
    return local_file

def inject_not_audio_file(filename="not-audio.txt"):
    """Create a file with .txt contents."""
    os.makedirs(TEST_INPUT_DIR, exist_ok=True)
    local_file = os.path.join(TEST_INPUT_DIR, filename)
    with open(local_file, "w") as f:
        f.write("This is not an audio file.")
    return local_file

def clean_test_input_dir():
    """Remove all files from the input/ dir."""
    if os.path.isdir(TEST_INPUT_DIR):
        for fname in os.listdir(TEST_INPUT_DIR):
            try:
                os.remove(os.path.join(TEST_INPUT_DIR, fname))
            except Exception:
                pass
