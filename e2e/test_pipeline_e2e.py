import subprocess
import requests
import time
import os

TEST_MP3_URL = (
    "https://rorecclesia.com/demo/wp-content/uploads/2024/12/01-Chosen.mp3"
)
TEST_FILENAME = "01-Chosen.mp3"
STATUS_API_URL = "http://localhost:5001"
ORGANIZED_DIR = "organized"  # Must match Docker volume mapping!


def wait_for_status_api(timeout=60):
    for _ in range(timeout):
        try:
            r = requests.get(f"{STATUS_API_URL}/health")
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def wait_for_file_status(filename, expected_status, timeout=180):
    for _ in range(timeout):
        try:
            r = requests.get(f"{STATUS_API_URL}/status")
            r.raise_for_status()
            files = r.json().get("files", [])
            for f in files:
                if (
                    f["filename"] == filename
                    and f["status"] == expected_status
                ):
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False


def test_full_pipeline_e2e(tmp_path):
    # --- Step 1: Ensure clean env
    subprocess.run(["docker", "compose", "down", "-v"], check=True)
    # --- Step 2: Start stack
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    assert wait_for_status_api(), "status-api /health did not become ready"

    # --- Step 3: Download and inject test file into input volume
    local_input_dir = os.path.join(os.getcwd(), "input")
    os.makedirs(local_input_dir, exist_ok=True)
    test_mp3 = os.path.join(local_input_dir, TEST_FILENAME)
    if not os.path.exists(test_mp3):
        print("Downloading test mp3...")
        r = requests.get(TEST_MP3_URL, timeout=60)
        r.raise_for_status()
        with open(test_mp3, "wb") as f:
            f.write(r.content)
    assert os.path.exists(test_mp3)

    # --- Step 4: Wait for pipeline to process file
    stages = ["queued", "metadata_extracted", "split", "packaged", "organized"]
    for stage in stages:
        assert wait_for_file_status(
            TEST_FILENAME, stage, timeout=90
        ), f"File did not reach stage: {stage}"

    # --- Step 5: Confirm final output exists in organized directory
    found = False
    for root, dirs, files in os.walk(os.path.join(os.getcwd(), ORGANIZED_DIR)):
        for file in files:
            if file.endswith("_karaoke.mp3"):
                found = True
                print(f"✅ Found output file: {os.path.join(root, file)}")
                break
    assert found, "Processed karaoke file not found in organized dir"

    # --- Step 6: Clean up containers
    subprocess.run(["docker", "compose", "down", "-v"], check=True)
