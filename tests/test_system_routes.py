from fastapi.testclient import TestClient

from device_management_service.main import app
from device_management_service.presentation.api import system_routes

client = TestClient(app)


def test_health_answers_without_the_database():
    assert client.get("/api/system/health").json() == {"status": "ok"}


def test_status_reaches_the_database():
    response = client.get("/api/system/status")

    assert response.status_code == 200
    assert response.json()["database"]["ok"] is True


def test_status_hides_the_error_detail_when_the_database_fails(monkeypatch):
    class BrokenEngine:
        def connect(self):
            raise RuntimeError("could not connect to ep-secreto.neon.tech")

    monkeypatch.setattr(system_routes, "engine", BrokenEngine())

    response = client.get("/api/system/status")

    assert response.status_code == 503
    assert response.json()["database"] == {"ok": False, "error": "RuntimeError"}
    assert "neon.tech" not in response.text
