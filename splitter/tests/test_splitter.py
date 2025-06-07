# splitter/tests/test_splitter.py
import pytest
from splitter.splitter import get_supported_stems, filter_and_export_stems
from unittest import mock
import os

def test_get_supported_stems():
    assert set(get_supported_stems("SPLEETER", 2)) == {"vocals", "accompaniment"}
    assert set(get_supported_stems("DEMUCS", 4)) == {"vocals", "drums", "bass", "other"}
    assert get_supported_stems("INVALID", 2) == []

def test_filter_and_export_stems(tmp_path):
    # Create fake stem files (wav format)
    stems_dir = tmp_path / "stems"
    stems_dir.mkdir()
    fake_wav = stems_dir / "vocals.wav"
    fake_wav.write_bytes(b"RIFF" + b"\0" * 1000)
    dest_dir = tmp_path / "exported"
    result = filter_and_export_stems(str(stems_dir), ["vocals"], str(dest_dir))
    assert "vocals" in result
    assert (dest_dir / "vocals.wav").exists()

def test_process_file_handles_error(monkeypatch):
    # Simulate process_file raising error and max retries hit
    from splitter import splitter
    monkeypatch.setenv("CHUNKING_ENABLED", "false")
    monkeypatch.setenv("MAX_RETRIES", "1")
    monkeypatch.setenv("RETRY_DELAY", "0")
    def bad_run(*a, **k): raise RuntimeError("fail")
    monkeypatch.setattr(splitter, "run_spleeter", bad_run)
    monkeypatch.setattr(splitter, "get_supported_stems", lambda *a, **k: ["vocals"])
    result = splitter.process_file("/tmp/foo.mp3", "foo")
    assert "fail" in result
