import time

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_p95_latency_under_200ms():
    samples = []
    for _ in range(30):
        start = time.perf_counter()
        resp = client.get("/v1/energy/commodity/price", params={"commodity": "WTI"})
        samples.append((time.perf_counter() - start) * 1000)
        assert resp.status_code in (200, 503)   # 503 only acceptable if truly no data yet

    samples.sort()
    p95 = samples[int(len(samples) * 0.95) - 1]
    assert p95 < 200, f"p95 latency was {p95:.1f}ms"
