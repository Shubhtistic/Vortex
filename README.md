# Vortex High-Throughput Telemetry Engine

> **DISCLAIMER:** This is an educational project designed to demonstrate high-throughput backend architecture and event-driven design patterns. It is not affiliated with, endorsed by, or associated with any existing "Vortex" commercial software, services, or companies. This project is for learning purposes only.

## 1. Executive Summary
Vortex is a high-performance backend system designed to ingest, process, and analyze massive streams of time-series data. It solves the "blocking I/O" problem inherent in monolithic APIs by implementing an **Event-Driven Architecture**.

The system separates **Ingestion** (FastAPI) from **Processing** (Celery + Redis), allowing it to handle traffic spikes of 10,000+ requests per second while maintaining sub-20ms response times.

**Primary Tech Stack:**
* **Language:** Python 3.12+
* **API Framework:** FastAPI (Async/Await)
* **Database:** PostgreSQL 16 (for structured storage)
* **Message Broker:** Redis (In-Memory Queue)
* **Task Queue:** Celery (Background Workers)

## 2. Architecture Overview

The system follows a Producer-Consumer pipeline:

1.  **Ingestion (Producer):** Client POSTs data to FastAPI. The server validates the payload and pushes it to Redis immediately. Response time: <20ms.
2.  **Buffering (Queue):** Redis holds the volatile data in RAM.
3.  **Processing (Consumer):** Celery workers pick up events from Redis asynchronously and perform the heavy "Write" operations to PostgreSQL.
4.  **Analysis:** Admin dashboards query PostgreSQL directly for aggregated insights.

## 3. Project Structure
The codebase follows the "Service Pattern" for scalability:

- `app/api`: API Route definitions (The "Controller" layer).
- `app/core`: Global configurations and security settings.
- `app/models`: Database table definitions (SQLModel).
- `app/schemas`: Pydantic models for request validation.
- `app/worker.py`: Background task definitions.

