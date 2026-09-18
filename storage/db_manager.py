import json

import psycopg2
import psycopg2.extras

import config


def get_conn():
    return psycopg2.connect(config.DATABASE_URL)


def insert_raw(conn, quote):
    """Store one successful raw observation, for audit/history purposes."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_ingest (commodity, source_id, publisher, payload, retrieved_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                quote.commodity,
                quote.source_id,
                quote.publisher,
                json.dumps(
                    {
                        "price": quote.price,
                        "currency": quote.currency,
                        "unit": quote.unit,
                        "as_of": quote.as_of.isoformat(),
                    }
                ),
                quote.retrieved_at,
            ),
        )
    conn.commit()


def insert_consensus(conn, commodity, tenor, data_block, meta_block, ttl_seconds):
    """Store the result of one consensus round - this is what the API will serve."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO consensus (commodity, tenor, data, meta, ttl_seconds)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (commodity, tenor, json.dumps(data_block), json.dumps(meta_block), ttl_seconds),
        )
    conn.commit()


def get_latest_consensus(conn, commodity, tenor):
    """The API only ever reads this - never touches the internet directly (keeps latency low)."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT data, meta, ttl_seconds, created_at
            FROM consensus
            WHERE commodity = %s AND tenor = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (commodity, tenor),
        )
        return cur.fetchone()


def purge_and_rollup(conn):
    """TTL lifecycle: summarize old raw rows into hourly rollups, then delete the raw rows."""
    rollup_seconds = config.ROLLUP_AFTER_SECONDS
    consensus_seconds = config.ROLLUP_AFTER_SECONDS * 2

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO rollup_history
                (commodity, period_start, period_end, avg_price, min_price, max_price, sample_count)
            SELECT
                commodity,
                date_trunc('hour', retrieved_at) AS period_start,
                date_trunc('hour', retrieved_at) + interval '1 hour' AS period_end,
                AVG((payload->>'price')::numeric),
                MIN((payload->>'price')::numeric),
                MAX((payload->>'price')::numeric),
                COUNT(*)
            FROM raw_ingest
            WHERE retrieved_at < now() - (%s * interval '1 second')
            GROUP BY commodity, date_trunc('hour', retrieved_at)
            ON CONFLICT (commodity, period_start) DO NOTHING
            """,
            (rollup_seconds,),
        )

        cur.execute(
            "DELETE FROM raw_ingest WHERE retrieved_at < now() - (%s * interval '1 second')",
            (rollup_seconds,),
        )
        # old consensus rows can go too - we already preserved history in rollup_history
        cur.execute(
            "DELETE FROM consensus WHERE created_at < now() - (%s * interval '1 second')",
            (consensus_seconds,),
        )
    conn.commit()
