from fastapi.testclient import TestClient

from evermind.api.main import app


def test_healthz_returns_exact_ok_response():
    response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
