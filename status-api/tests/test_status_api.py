# status-api/tests/test_status_api.py
from status_api.status_api import app


def test_healthcheck():
    with app.test_client() as c:
        resp = c.get("/health")
        assert resp.status_code == 200


def test_metrics_format():
    with app.test_client() as c:
        resp = c.get("/metrics")
        assert resp.status_code == 200
        assert "karaoke_statusapi_uptime_seconds" in resp.data.decode()


def test_status_endpoint_mocks(monkeypatch):
    # Patch get_files_by_status to simulate files at each stage
    from status_api import status_api

    monkeypatch.setattr(
        status_api,
        "get_files_by_status",
        lambda s: ["file1.mp3"] if s == "queued" else [],
    )
    with app.test_client() as c:
        resp = c.get("/status")
        assert resp.status_code == 200
        assert "files" in resp.get_json()
