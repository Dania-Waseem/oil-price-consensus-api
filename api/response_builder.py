import uuid
from datetime import datetime, timezone

import config


def build_envelope(row: dict, latency_ms: float) -> dict:
    """row = {'data':.., 'meta':.., 'ttl_seconds':.., 'created_at':..} straight from Postgres."""
    now = datetime.now(timezone.utc)
    source_time = datetime.fromisoformat(row["meta"]["source_last_updated_at"])
    age_seconds = int((now - source_time).total_seconds())
    stale = age_seconds > row["ttl_seconds"]

    return {
        "data": row["data"],
        "meta": {
            "request_id": f"req_{uuid.uuid4().hex[:20]}",
            "product_id": row["meta"]["product_id"],
            "version": row["meta"]["version"],
            "served_at": now.isoformat(),
            "source_last_updated_at": row["meta"]["source_last_updated_at"],
            "freshness": {
                "age_seconds": age_seconds,
                "ttl_seconds": row["ttl_seconds"],
                "stale": stale,
            },
            "provenance": row["meta"]["provenance"],
            "trust": row["meta"]["trust"],
            "license": {"type": "commercial", "usage": "agent_runtime"},
            "api": {"latency_ms": latency_ms, "rate_limit": config.RATE_LIMIT},
            "warnings": row["meta"]["warnings"],
        },
    }
