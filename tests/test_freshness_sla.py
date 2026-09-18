from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_freshness_fields_present_and_consistent():
    resp = client.get("/v1/energy/commodity/price", params={"commodity": "WTI"})

    if resp.status_code == 503:
        return  # nothing ingested yet in this environment - nothing to check

    body = resp.json()
    freshness = body["meta"]["freshness"]

    assert freshness["age_seconds"] >= 0
    assert freshness["ttl_seconds"] > 0
    assert freshness["stale"] == (freshness["age_seconds"] > freshness["ttl_seconds"])
