# WTI Consensus Oracle

Live WTI oil price feed with multi-source consensus, standardized agent-ready REST payload,
PostgreSQL/JSONB storage with TTL lifecycle, and an SLA test suite.

Endpoint: `GET /v1/energy/commodity/price?commodity=WTI&tenor=spot`

## 0. Prerequisites

- Python 3.10+
- Docker Desktop (easiest way to get Postgres running without installing it natively)

## 1. Start Postgres (via Docker - no native install needed)

```bash
docker compose up -d
```

This starts a Postgres 16 container on `localhost:5432` with user `oiluser`, password `oilpass`,
database `oildata` (matches `.env.example`). Data persists in a Docker volume between restarts.

To confirm it's running: `docker ps` should show a `db` container as "healthy"/"Up".

(If you'd rather install Postgres natively instead of Docker, install it from postgresql.org,
then create a database and user matching `.env.example`, and skip the `docker compose` step.)

## 2. Get a free Alpha Vantage API key (our second data source)

1. Go to `https://www.alphavantage.co/support/#api-key`
2. Enter your email, click "GET FREE API KEY" - it appears instantly, no card, no CAPTCHA.
3. Keep it handy for Step 3 below.

(Our first source, Yahoo Finance, needs no key at all.)

## 3. Python environment

```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Now open `.env` and paste your Alpha Vantage key in place of `your_key_here`.

## 4. Create the database tables

```bash
python db/init_db.py
```

You should see `Database schema created successfully.`

## 5. Run the background worker (keep this running in its own terminal)

```bash
python -m worker.background_worker
```

This fetches WTI prices from two providers every 60 seconds, runs consensus, and writes to
Postgres. Let it run for at least one cycle before hitting the API.

## 6. Run the API (in a second terminal)

```bash
uvicorn api.main:app --reload
```

Then visit: `http://localhost:8000/v1/energy/commodity/price?commodity=WTI`

Interactive API docs are auto-generated at `http://localhost:8000/docs`.

## 7. Run the test suite

```bash
pytest -v
```

(`test_availability.py`, `test_latency.py`, and `test_freshness_sla.py` need the API + DB
reachable; `test_consensus.py` and `test_failover.py` are pure unit tests and need nothing
running at all.)

## How it satisfies the assignment requirements

| Requirement | Where |
|---|---|
| Multi-source ingestion | `ingestion/source_yahoo.py`, `ingestion/source_alphavantage.py` |
| Consensus + confidence/quality score | `consensus/consensus_engine.py` |
| No silent fallbacks | `SourceError` / `ConsensusError` raised explicitly, never caught-and-ignored |
| Standardized payload | `api/response_builder.py` |
| PostgreSQL + JSONB storage | `db/schema.sql`, `storage/db_manager.py` |
| TTL purge / rollup | `storage/db_manager.py::purge_and_rollup` |
| SLA tests | `tests/` |
