# Vortex Telemetry Engine

> A production-grade, self-hosted telemetry pipeline. Ingest user events at scale, own your data, pay nothing to third parties.

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-black.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-black.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-black.svg)](https://docker.com)

---

## The Problem

Companies pay thousands of dollars a month to Segment, Mixpanel, and PostHog just to track their own users' clicks. Beyond cost, every event you send to a third-party SaaS is data you no longer fully own.

**Vortex is the alternative.** Self-host a professional telemetry pipeline on your own infrastructure. One `docker compose up` and you have a production-ready event ingestion and analytics backend.

---

## Features

- **Non-blocking ingestion** — FastAPI accepts events and writes them directly to Redis. The HTTP response is returned immediately. The database write happens asynchronously in batches.
- **Multi-tenant by design** — every tenant gets isolated public/secret API key pairs. Data is strictly scoped per tenant at the query level.
- **Per-tenant rate limiting** — atomic Redis counters enforce request limits before any payload is written to PostgreSQL.
- **Separation of powers** — Public Keys can only write. Secret Keys can only read. Enforced at the endpoint level.
- **Runs on free-tier hardware** — verified at 136.5 req/sec sustained on an AWS EC2 `t2.micro`.

---

## Architecture

```
Client (vtx_pub_...)
        │
        ▼
  POST /api/v1/track
        │
   Rate Limit Check (Redis)
        │
   Push to Redis List (vortex_buffer)
        │
   202 Accepted ──► Client
        │
   ARQ Worker sweeps batch (every 5s)
        │
   Bulk INSERT into PostgreSQL
```

Analytics reads (`vtx_sec_...`) go directly from FastAPI to PostgreSQL with tenant-level row isolation.

---

## Architecture Evolution: Celery to ARQ

Initially, Vortex used **Celery** as its background task queue. While Celery is an industry standard, it is fundamentally synchronous and relies on thread/process pooling to handle concurrency.

As the engine scaled to handle thousands of async FastAPI requests, Celery caused two core problems:

- **Event loop conflicts** — running `asyncio` database drivers (`asyncpg`) inside Celery caused "Task attached to a different loop" crashes at runtime.
- **Connection pool leaks** — sharing SQLAlchemy `QueuePool` configurations between the FastAPI process and the isolated worker container caused ghost connections and database lockups.

**The ARQ solution** migrates the entire background processing layer to **ARQ**, a job queue built natively for Python's `asyncio` and `redis.asyncio`. This enabled a true zero-data-loss batching pipeline:

1. **FastAPI** — accepts JSON payloads and writes them to Redis via `RPUSH` in ~1ms without touching the database.
2. **Atomic swap** — the ARQ worker wakes every 5 seconds and runs a `RENAME` on the Redis list. This O(1) operation guarantees zero race conditions with incoming API traffic.
3. **Isolated worker** — using SQLAlchemy's `NullPool` inside the ARQ context, the worker opens a single isolated database connection, bulk-inserts all pending events, closes the connection, and deletes the processed Redis key.

The result is a pipeline that handles large traffic spikes without exhausting database connections or blocking the main API event loop.

---

## Quickstart

### Prerequisites

- Docker and Docker Compose
- Git

### 1. Clone and configure

```bash
git clone https://github.com/Shubhtistic/vortex-telemetry-engine.git
cd vortex-telemetry-engine
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
POSTGRES_SERVER=postgres_database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=vortex_db
REDIS_URL=redis://redis:6379/0
DOCS_ENDPOINT=your_docs_secret_here
```

### 2. Start the stack

```bash
# Development
docker compose up --build

# Production (detached)
docker compose -f compose.prod.yml up -d --build
```

Docker boots services in dependency order automatically:

| Step | Services | Condition |
|------|----------|-----------|
| 1 | `postgres_database` + `redis` | Start immediately in parallel |
| 2 | `migrate` | Waits for postgres healthcheck, runs migrations, then exits |
| 3 | `api` + `worker` | Start after migrate exits successfully |

---

## API Reference

All endpoints require an `X-API-Key` header.

| Method | Endpoint | Key Type | Description |
|--------|----------|----------|-------------|
| `POST` | `/api/v1/track` | Public (`vtx_pub_...`) | Ingest a new event |
| `GET` | `/api/v1/stats` | Secret (`vtx_sec_...`) | Aggregate event counts |
| `GET` | `/api/v1/top-urls` | Secret (`vtx_sec_...`) | Top visited URLs for a tenant |
| `GET` | `/api/v1/events-per-day` | Secret (`vtx_sec_...`) | Time-series event data |
| `GET` | `/api/v1/verify` | Secret (`vtx_sec_...`) | Verify a secret key |

### Example — track an event

```bash
curl -X POST https://your-domain.com/api/v1/track \
  -H "X-API-Key: vtx_pub_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://yourapp.com/pricing",
    "event_type": "page_view",
    "payload": {
      "session_id": "abc123",
      "country": "IN"
    }
  }'
```

**Response:** `202 Accepted`

---

## Tenant Management

Use the built-in CLI wizard to create tenants and manage API keys. No direct database access needed.

```bash
docker compose exec -it api python -m app.cli
```

The wizard creates a tenant and generates a `vtx_pub_` / `vtx_sec_` key pair. The secret key is shown only once — store it immediately.

---

## Deployment Options

| Strategy | Compute | Database | Cache |
|----------|---------|----------|-------|
| All-in-One | EC2 / Any VPS | Docker Container | Docker Container |
| Production Standard | EC2 (Dockerized) | AWS RDS | Docker Container |
| Full Managed | EC2 Auto-scaling | AWS RDS | AWS ElastiCache |
| Zero-Cost | Render / Railway | Neon.tech / Supabase | Upstash Redis |

The project is verified on **AWS EC2 `t2.micro` + AWS RDS** within the AWS Free Tier.

For the zero-cost path, point `.env` at a [Neon.tech](https://neon.tech) Postgres URL and an [Upstash](https://upstash.com) Redis URL. No other changes needed.

---

## Performance

Load tested with [Grafana k6](https://k6.io) using 70 concurrent virtual users across 15 tenants on a `t2.micro`.

| Metric | Result |
|--------|--------|
| Total requests (5 min) | ~40,391 |
| Sustained throughput | **134.5 req/sec** |
| Ingestion latency p(95) | **45.0 ms** |
| True error rate | ~0% |

> IMP NOTE: We observed an error rate of 37.8% in raw results, which is exclusively due to `429 Too Many Requests` from the rate limiter working correctly — not application failures.

---

## Stack

- **[FastAPI](https://fastapi.tiangolo.com)** — async HTTP layer
- **[ARQ](https://arq-docs.helpmanual.io/)** — native asyncio job queue
- **[Redis](https://redis.io)** — high-speed buffer and rate limit counters
- **[PostgreSQL](https://postgresql.org)** — persistent event storage
- **[Alembic](https://alembic.sqlalchemy.org)** — database migrations
- **[Docker Compose](https://docs.docker.com/compose)** — orchestration

---

## Monitoring

```bash
# Live API logs
docker compose logs -f api

# ARQ worker logs
docker compose logs -f worker

# Surface non-standard errors only
docker compose logs api \
  | grep "HTTP/1" \
  | grep -v " 200 " \
  | grep -v " 202 " \
  | grep -v " 429 "
```

---

## Future Improvements

- [ ] JavaScript SDK (`vortex.track()`)
- [ ] Origin allowlisting (per-tenant CORS enforcement)
- [ ] ClickHouse / TimescaleDB support for high-volume deployments

---

## Contributing

Pull requests are welcome. For major changes please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)