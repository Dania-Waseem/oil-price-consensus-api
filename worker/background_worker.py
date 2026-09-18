import time

import config
from consensus.consensus_engine import ConsensusError, compute_consensus
from ingestion import source_alphavantage, source_yahoo
from ingestion.base import SourceError
from storage import db_manager

# Yahoo has no meaningful rate limit for our purposes, so we call it every cycle.
# Alpha Vantage's free tier only allows 25 calls/day, so we cache its last good
# quote and only refetch every ALPHA_VANTAGE_EVERY_N_CYCLES cycles.
_cached_av_quote = None


def get_alpha_vantage_quote(cycle_count):
    global _cached_av_quote
    due_for_refetch = (cycle_count % config.ALPHA_VANTAGE_EVERY_N_CYCLES == 0) or (_cached_av_quote is None)

    if due_for_refetch:
        _cached_av_quote = source_alphavantage.fetch()   # lets SourceError propagate to caller
        return _cached_av_quote, True   # True = freshly fetched this cycle (worth storing raw)

    if _cached_av_quote is None:
        raise SourceError("alphavantage", "no cached quote available yet")

    return _cached_av_quote, False


def run_one_cycle(conn, cycle_count):
    quotes, errors = [], []

    try:
        yahoo_quote = source_yahoo.fetch()
        quotes.append(yahoo_quote)
        db_manager.insert_raw(conn, yahoo_quote)
    except SourceError as e:
        errors.append({"source_id": e.source_id, "reason": e.reason})
        print(f"[warning] source failed: {e}")

    try:
        av_quote, was_fresh = get_alpha_vantage_quote(cycle_count)
        quotes.append(av_quote)
        if was_fresh:
            db_manager.insert_raw(conn, av_quote)
    except SourceError as e:
        errors.append({"source_id": e.source_id, "reason": e.reason})
        print(f"[warning] source failed: {e}")

    try:
        result = compute_consensus(quotes, errors)
    except ConsensusError as e:
        # nothing trustworthy to store this round - never invent a fresh-looking number
        print(f"[error] consensus failed this cycle: {e}")
        return

    data_block = {
        "commodity": config.COMMODITY,
        "tenor": config.TENOR,
        "price": result["price"],
        "currency": config.CURRENCY,
        "unit": config.UNIT,
        "as_of": result["source_last_updated_at"].isoformat(),
    }
    meta_block = {
        "product_id": config.PRODUCT_ID,
        "version": config.API_VERSION,
        "source_last_updated_at": result["source_last_updated_at"].isoformat(),
        "provenance": result["provenance"],
        "trust": {
            "confidence": result["confidence"],
            "quality_score": result["quality_score"],
            "verified": result["verified"],
        },
        "warnings": result["warnings"],
    }

    db_manager.insert_consensus(
        conn, config.COMMODITY, config.TENOR, data_block, meta_block, config.TTL_SECONDS
    )
    print(f"[ok] stored consensus price={result['price']} confidence={result['confidence']}")


def main():
    conn = db_manager.get_conn()
    last_purge = 0.0
    cycle_count = 0

    while True:
        run_one_cycle(conn, cycle_count)
        cycle_count += 1

        if time.time() - last_purge > 3600:   # run TTL cleanup once an hour
            db_manager.purge_and_rollup(conn)
            last_purge = time.time()

        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
