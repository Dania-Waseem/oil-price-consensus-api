-- Every raw price observation, one row per (provider, fetch)
CREATE TABLE IF NOT EXISTS raw_ingest (
    id BIGSERIAL PRIMARY KEY,
    commodity TEXT NOT NULL,
    source_id TEXT NOT NULL,
    publisher TEXT NOT NULL,
    payload JSONB NOT NULL,           -- {"price":.., "currency":.., "unit":.., "as_of":..}
    retrieved_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_raw_commodity_time ON raw_ingest (commodity, retrieved_at);
CREATE INDEX IF NOT EXISTS idx_raw_payload_gin ON raw_ingest USING GIN (payload);

-- One row per finished consensus round (this is what the API reads from)
CREATE TABLE IF NOT EXISTS consensus (
    id BIGSERIAL PRIMARY KEY,
    commodity TEXT NOT NULL,
    tenor TEXT NOT NULL,
    data JSONB NOT NULL,               -- the "data" block of the response
    meta JSONB NOT NULL,               -- provenance/trust/warnings (freshness computed live)
    ttl_seconds INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_consensus_commodity_time ON consensus (commodity, tenor, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_consensus_data_gin ON consensus USING GIN (data);

-- Compressed history: hourly summaries of raw data that has aged out
CREATE TABLE IF NOT EXISTS rollup_history (
    id BIGSERIAL PRIMARY KEY,
    commodity TEXT NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    avg_price NUMERIC,
    min_price NUMERIC,
    max_price NUMERIC,
    sample_count INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (commodity, period_start)
);
