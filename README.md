# Vortex

Vortex is a hybrid Mixpanel-style analytics product: clients emit events, the backend normalizes and derives identity/group relationships, stores analytics data, and the dashboard provides reporting.

## Broker plan

- Moving the event processing pipeline to Redpanda as the message broker.
- Running a parallel trial of Apache Iggy to compare behavior with the same real event shape.

## Repository

- Backend: FastAPI
- Storage: Postgres
- Frontend: Next.js

