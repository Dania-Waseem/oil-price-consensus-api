import statistics
from datetime import datetime, timezone

import config
from ingestion.base import RawQuote


class ConsensusError(Exception):
    """Raised when we truly have nothing usable. Must propagate - never fabricate a number."""


def compute_consensus(quotes: list[RawQuote], errors: list[dict]) -> dict:
    """
    quotes: providers that answered successfully this round (0, 1, or 2+)
    errors: [{"source_id":..., "reason":...}] for providers that failed this round
    Returns a dict with the final price + trust metadata, ready to store/serve.
    """
    warnings = [f"{e['source_id']} failed: {e['reason']}" for e in errors]

    if not quotes:
        # Total failure this round. We do NOT invent a number.
        raise ConsensusError("all sources failed this round: " + "; ".join(warnings))

    # step 1: use the MEDIAN as the reference point for outlier detection.
    # (the mean itself can be dragged off by a single bad outlier - median can't)
    reference_price = statistics.median(q.price for q in quotes)

    # step 2: drop anything too far from that reference point
    kept, dropped = [], []
    for q in quotes:
        deviation = abs(q.price - reference_price) / reference_price
        (kept if deviation <= config.OUTLIER_THRESHOLD_PCT else dropped).append(q)

    for q in dropped:
        warnings.append(f"{q.source_id} rejected as outlier ({q.price} vs median {reference_price:.2f})")

    if not kept:
        # every quote disagreed wildly - don't fake a "truth"
        raise ConsensusError("no sources agreed within tolerance: " + "; ".join(warnings))

    final_price = _weighted_mean(kept)

    # step 3: confidence = fraction of ALL expected sources that actually agreed
    confidence = round(len(kept) / max(len(quotes) + len(errors), 1), 2)

    # step 4: quality penalizes stale inputs and missing sources
    freshest_gap = min((datetime.now(timezone.utc) - q.as_of).total_seconds() for q in kept)
    quality_score = round(
        max(0.0, 1.0 - (freshest_gap / config.TTL_SECONDS) * 0.3 - len(errors) * 0.1), 2
    )

    verified = len(kept) >= 2  # only "verified" if at least 2 independent sources agreed

    provenance = [
        {"source_id": q.source_id, "publisher": q.publisher, "retrieved_at": q.retrieved_at.isoformat()}
        for q in kept
    ]
    freshest_source_time = max(q.as_of for q in kept)

    return {
        "price": round(final_price, 2),
        "source_last_updated_at": freshest_source_time,
        "confidence": confidence,
        "quality_score": quality_score,
        "verified": verified,
        "provenance": provenance,
        "warnings": warnings,
    }


def _weighted_mean(quotes: list[RawQuote]) -> float:
    total, total_weight = 0.0, 0.0
    for q in quotes:
        provider_key = q.source_id.split("-")[1].lower()   # "SRC-YAHOO-CLF" -> "yahoo"
        weight = config.SOURCE_WEIGHTS.get(provider_key, 1.0)
        total += q.price * weight
        total_weight += weight
    return total / total_weight
