from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_available_under_repeated_polling():
    for _ in range(20):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
