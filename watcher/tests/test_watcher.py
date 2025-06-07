# watcher/tests/test_watcher.py
import tempfile
import shutil
import os
import pytest
from unittest import mock
from watcher.watcher import MP3Handler, app

def test_healthcheck():
    with app.test_client() as c:
        resp = c.get("/health")
        assert resp.status_code == 200

def test_mp3_detection_and_queueing(tmp_path):
    handler = MP3Handler()
    mp3 = tmp_path / "test.mp3"
    mp3.write_bytes(b"ID3" + b"\0" * 1000)
    with mock.patch("watcher.watcher.set_file_status") as m_set_status, \
         mock.patch("watcher.watcher.clean_string", side_effect=lambda x: x):
        event = mock.Mock()
        event.is_directory = False
        event.src_path = str(mp3)
        handler.on_created(event)
        m_set_status.assert_called_once_with("test.mp3", "queued")

def test_ignore_non_mp3_files(tmp_path):
    handler = MP3Handler()
    txt = tmp_path / "ignore.txt"
    txt.write_text("hello")
    with mock.patch("watcher.watcher.set_file_status") as m_set_status, \
         mock.patch("watcher.watcher.clean_string", side_effect=lambda x: x):
        event = mock.Mock()
        event.is_directory = False
        event.src_path = str(txt)
        handler.on_created(event)
        m_set_status.assert_not_called()

def test_error_file_excluded(tmp_path):
    handler = MP3Handler()
    mp3 = tmp_path / "err.mp3"
    mp3.write_bytes(b"ID3" + b"\0" * 1000)
    with mock.patch("watcher.watcher.get_files_by_status", return_value=["err.mp3"]), \
         mock.patch("watcher.watcher.set_file_status") as m_set_status, \
         mock.patch("watcher.watcher.clean_string", side_effect=lambda x: x):
        event = mock.Mock()
        event.is_directory = False
        event.src_path = str(mp3)
        handler.on_created(event)
        m_set_status.assert_not_called()
