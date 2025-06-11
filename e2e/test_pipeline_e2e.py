import os
import pytest
from pipeline_test_utils import (
    wait_for_status_api,
    wait_for_file_status,
    inject_mp3_from_url,
    inject_corrupted_mp3,
    inject_not_audio_file,
    clean_test_input_dir,
)

# Test file definitions (remote file must exist)
VALID_MP3_URL = "https://rorecclesia.com/demo/wp-content/uploads/2024/12/01-Chosen.mp3"
VALID_MP3_FILENAME = "01-Chosen.mp3"
CORRUPTED_MP3_FILENAME = "corrupted.mp3"
NOT_AUDIO_FILENAME = "not-audio.txt"

# Define the E2E test scenarios
TEST_CASES = [
    {
        "desc": "Valid MP3 end-to-end",
        "prepare": lambda: inject_mp3_from_url(VALID_MP3_URL, VALID_MP3_FILENAME),
        "filename": VALID_MP3_FILENAME,
        "expected_stages": [
            "queued", "metadata_extracted", "split", "packaged", "organized"
        ],
        "should_pass": True,
    },
    {
        "desc": "Corrupted MP3 should fail before packaging",
        "prepare": lambda: inject_corrupted_mp3(CORRUPTED_MP3_FILENAME),
        "filename": CORRUPTED_MP3_FILENAME,
        "expected_stages": [
            "queued", "metadata_extracted"
        ],
        "should_pass": False,
        "fail_stage": "split",  # Should not make it to split stage
    },
    {
        "desc": "Non-audio file should fail at metadata",
        "prepare": lambda: inject_not_audio_file(NOT_AUDIO_FILENAME),
        "filename": NOT_AUDIO_FILENAME,
        "expected_stages": [
            "queued"
        ],
        "should_pass": False,
        "fail_stage": "metadata_extracted",  # Should not make it to metadata_extracted
    }
]

@pytest.fixture(scope="function", autouse=True)
def setup_and_cleanup():
    clean_test_input_dir()
    yield
    clean_test_input_dir()

@pytest.mark.parametrize("case", TEST_CASES)
def test_pipeline_file_handling(case):
    print(f"\n=== Running: {case['desc']} ===")
    assert wait_for_status_api(), "status-api /health did not become ready"
    local_file = case["prepare"]()
    assert os.path.exists(local_file), f"Test file {local_file} was not created"

    for idx, stage in enumerate(case["expected_stages"]):
        result = wait_for_file_status(case["filename"], stage, timeout=90)
        if not case["should_pass"]:
            # For negative tests, check that we do NOT reach the next stage (fail_stage)
            if "fail_stage" in case and idx + 1 < len(case["expected_stages"]):
                # Should not reach the next stage
                next_stage = case["expected_stages"][idx + 1]
                fail_result = wait_for_file_status(case["filename"], next_stage, timeout=20)
                assert not fail_result, (
                    f"{case['desc']} - File {case['filename']} "
                    f"should NOT reach stage: {next_stage}"
                )
        assert result, (
            f"{case['desc']} - File {case['filename']} did not reach stage: {stage}"
        )

    # For negative test, confirm that fail_stage is NOT reached
    if not case["should_pass"] and "fail_stage" in case:
        fail_result = wait_for_file_status(case["filename"], case["fail_stage"], timeout=20)
        assert not fail_result, (
            f"{case['desc']} - File {case['filename']} should NOT reach fail stage: {case['fail_stage']}"
        )
