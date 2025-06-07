# tests/test_pipeline_integration.py
import pytest
import requests
import time
import os

def test_pipeline_happy_path(tmp_path):
    # Download test asset (if not already present)
    url = "https://rorecclesia.com/demo/wp-content/uploads/2024/12/01-Chosen.mp3"
    mp3_path = tmp_path / "01-Chosen.mp3"
    if not mp3_path.exists():
        r = requests.get(url, timeout=30)
        mp3_path.write_bytes(r.content)
    assert mp3_path.exists()
    # Simulate: place in watcher input dir
    # If pipeline is running, file should flow through all stages
    # This can be expanded as real pipeline integration matures
    # For now: just check we can fetch the asset and assert file exists
