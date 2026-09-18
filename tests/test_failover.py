from datetime import datetime, timezone

from consensus.consensus_engine import compute_consensus
from ingestion.base import RawQuote


def test_consensus_survives_one_source_down():
    quotes = [
        RawQuote(
            source_id="SRC-YAHOO-CLF",
            publisher="test",
            commodity="WTI",
            price=68.2,
            currency="USD",
            unit="barrel",
            as_of=datetime.now(timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
        )
    ]
    errors = [{"source_id": "SRC-STOOQ-CLF", "reason": "timeout"}]

    result = compute_consensus(quotes, errors)

    assert result["price"] == 68.2
    assert result["verified"] is False              # only 1 source, so not "verified"
    assert result["confidence"] < 1.0                # confidence reflects the missing source
    assert any("stooq" in w.lower() for w in result["warnings"])   # failure is visible, not hidden
