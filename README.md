# Vortex Telemetry Engine

> A production-grade, self-hosted telemetry pipeline. Ingest user events at scale, own your data, pay nothing to third parties.

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-black.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-black.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-black.svg)](https://docker.com)

---

## The Problem

Companies pay thousands of dollars a month to Segment, Mixpanel, and PostHog — just to track their own users' clicks. Beyond cost, every event you send to a third-party SaaS is data you no longer fully own.

**Vortex is the alternative.** Self-host a professional telemetry pipeline on your own infrastructure. One `docker compose up` and you have a production-ready event ingestion and analytics backend.

---

## Features

- **Non-blocking ingestion** — FastAPI accepts events and hands them to Celery via Redis. The HTTP response is returned in single-digit milliseconds; the database write happens asynchronously.
- **Multi-tenant by design** — every tenant gets isolated pub/sec API key pairs. Data is strictly scoped per tenant at the query level.
- **Per-tenant rate limiting** — atomic Redis counters enforce request limits before any payload ever touches PostgreSQL.
- **Separation of powers** — Public Keys can only write. Secret Keys can only read. Enforced at the endpoint level.
- **Runs on free-tier hardware** — verified at 131.5 req/sec sustained on an AWS EC2 `t2.micro`.

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
   Push to Task Queue (Redis)
        │
   202 Accepted ──► Client
        │
   Celery Worker pulls task
        │
   INSERT into PostgreSQL
```

**Analytics reads** (`vtx_sec_...`) go directly from FastAPI to PostgreSQL with tenant-level row isolation.

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
# Development (hot reload enabled)
docker compose up --build

# Production (detached)
docker compose -f compose.prod.yml up -d --build
```

Docker will boot services in dependency order automatically:

| Step | Services | Condition |
|------|----------|-----------|
| 1 | `postgres_database` + `redis` | Start immediately in parallel |
| 2 | `migrate` | Waits for postgres healthcheck, runs migrations, exits |
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

Use the built-in CLI wizard to create tenants and manage API keys. No direct database access required.

```bash
docker compose exec -it api python -m app.cli
```

The wizard will create a tenant and generate a `vtx_pub_` / `vtx_sec_` key pair. **The secret key is shown only once** — store it in a secrets manager immediately.

---

## Deployment Options

| Strategy | Compute | Database | Cache |
|----------|---------|----------|-------|
| All-in-One | EC2 / Any VPS | Docker Container | Docker Container |
| Production Standard | EC2 (Dockerized) | **AWS RDS** | Docker Container |
| Full Managed | EC2 Auto-scaling | AWS RDS | AWS ElastiCache |
| Zero-Cost | Render / Railway | Neon.tech / Supabase | Upstash Redis |

The project is verified on **AWS EC2 `t2.micro` + AWS RDS** within the AWS Free Tier.

For the zero-cost path, point `.env` at a [Neon.tech](https://neon.tech) Postgres URL and an [Upstash](https://upstash.com) Redis URL — no other changes needed.

---

## Performance

Load tested with [Grafana k6](https://k6.io) — 70 concurrent virtual users across 10 tenants on a `t2.micro`.

| Metric | Result |
|--------|--------|
| Total requests (5 min) | ~39,463 |
| Sustained throughput | **131.5 req/sec** |
| Ingestion latency p(95) | **84.0 ms** |
| True error rate | ~0% |

> The 37.8% observed error rate in raw results is exclusively `429 Too Many Requests` from the rate limiter functioning correctly — not application failures.

---

## Stack

- **[FastAPI](https://fastapi.tiangolo.com)** — async HTTP layer
- **[Celery](https://docs.celeryq.dev)** — distributed task queue
- **[Redis](https://redis.io)** — task broker and rate limit counters
- **[PostgreSQL](https://postgresql.org)** — persistent event storage
- **[Alembic](https://alembic.sqlalchemy.org)** — database migrations
- **[Docker Compose](https://docs.docker.com/compose)** — orchestration

---

## Monitoring

```bash
# Live API logs
docker compose logs -f api

# Celery worker logs
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

- [ ] Implement Redis-backed batching (Bulk SQL Inserts) to reduce database I/O.
- [ ] Migrate from Celery to ARQ for native `asyncio` worker performance.
- [ ] JavaScript SDK (`vortex.track()`).
- [ ] Origin allowlisting (per-tenant CORS enforcement).
- [ ] ClickHouse / TimescaleDB support for high-volume deployments.
---

## Contributing

Pull requests are welcome. For major changes please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)