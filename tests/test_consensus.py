from datetime import datetime, timezone

from consensus.consensus_engine import ConsensusError, compute_consensus
from ingestion.base import RawQuote


def make_quote(source_id, price):
    return RawQuote(
        source_id=source_id,
        publisher="test",
        commodity="WTI",
        price=price,
        currency="USD",
        unit="barrel",
        as_of=datetime.now(timezone.utc),
        retrieved_at=datetime.now(timezone.utc),
    )


def test_agreeing_sources_average_out():
    quotes = [make_quote("SRC-YAHOO-CLF", 68.0), make_quote("SRC-STOOQ-CLF", 68.2)]
    result = compute_consensus(quotes, [])
    assert 68.0 <= result["price"] <= 68.2
    assert result["verified"] is True


def test_outlier_is_rejected():
    quotes = [
        make_quote("SRC-YAHOO-CLF", 68.0),
        make_quote("SRC-STOOQ-CLF", 68.2),
        make_quote("SRC-BADFEED-CLF", 999.0),
    ]
    result = compute_consensus(quotes, [])
    assert 67 < result["price"] < 69
    assert any("outlier" in w for w in result["warnings"])


def test_total_failure_raises_explicitly():
    try:
        compute_consensus([], [{"source_id": "SRC-YAHOO-CLF", "reason": "down"}])
        assert False, "should have raised ConsensusError"
    except ConsensusError:
        pass
