# organizer/tests/test_organizer.py
from organizer.organizer import is_valid_karaoke_mp3, app


def test_healthcheck():
    with app.test_client() as c:
        resp = c.get("/health")
        assert resp.status_code == 200


def test_is_valid_karaoke_mp3():
    assert is_valid_karaoke_mp3("foo_karaoke.mp3")
    assert not is_valid_karaoke_mp3("foo.mp3")


def test_organize_file_creates_structure(tmp_path, monkeypatch):
    # Setup dummy mp3 file and metadata json
    output = tmp_path / "output"
    output.mkdir()
    org = tmp_path / "organized"
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    mp3 = output / "file_karaoke.mp3"
    mp3.write_bytes(b"ID3" + b"\0" * 1000)
    meta = meta_dir / "file.mp3.json"
    meta.write_text('{"TPE1":"Art","TALB":"Alb","TIT2":"Title"}')
    monkeypatch.setattr("organizer.organizer.ORG_DIR", str(org))
    monkeypatch.setattr("organizer.organizer.META_DIR", str(meta_dir))
    from organizer.organizer import organize_file

    organize_file(str(mp3), "file.mp3")
    dest = org / "Art" / "Alb" / "file_karaoke.mp3"
    assert dest.exists()
