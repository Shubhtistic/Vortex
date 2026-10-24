# Vortex Frontend

The frontend is the account and analytics interface for Vortex. It provides the public landing, signup, and login pages, plus an authenticated dashboard for organization analytics, members, tenants, API keys, and account details.

[Project overview](../README.md) · [Backend guide](../backend/README.md)

## Pages

| Route | Description |
|---|---|
| `/` | Public landing page; signed-in users are redirected to the dashboard. |
| `/signup` | Create an organization and initial account. |
| `/login` | Sign in using an organization slug, email, and password. |
| `/terms` | Terms and conditions page. |
| `/dashboard` | Analytics overview, filters, charts, event rankings, breakdowns, recent events, and workspace counts. |
| `/dashboard/members` | List, invite, and deactivate organization members. |
| `/dashboard/tenants` | List and create tenants. |
| `/dashboard/tenants/[id]` | View tenant details and manage API keys. |
| `/dashboard/settings` | Read-only signed-in account and organization details. |

Dashboard routes share `DashboardShell`, which provides the top navigation and persistent bottom dock. `ProtectedRoute` guards authenticated pages.

## Frontend structure

```text
src/
├── app/                 # Next.js App Router pages and dashboard route group
├── components/
│   ├── dashboard/       # Dashboard shell, dock, and analytics chart
│   └── ui/              # Reusable buttons, cards, forms, tables, and status UI
├── lib/
│   ├── api.ts           # Axios client, auth headers, refresh retry, validation errors
│   ├── auth-context.tsx # Access-token and current-user state
│   └── validation.ts    # Client input validation and sanitization
└── services/
    ├── api.services.ts  # Typed calls to backend endpoints
    └── api.types.ts     # Request and response types
```

## API and session behavior

The backend origin comes from the private `BACKEND_API_URL` environment variable. Next.js rewrites supported API paths through the frontend origin, so the backend origin is not compiled into browser JavaScript. The shared Axios client sends the `ngrok-skip-browser-warning` header and includes credentials for the refresh-token cookie. When available, it attaches the access token as a Bearer token. On an eligible `401`, it calls `/auth/refresh`, updates the in-memory access token, and retries the failed request.

The dashboard uses the backend analytics read routes: overview, timeseries, top events, breakdown, active users, and recent events. It sends a date range and can optionally narrow results by tenant and event name. The frontend does not call `POST /events`; event ingestion is intended for product clients and server applications using tenant API keys.

Supported API calls and their response types are kept in `src/services/api.services.ts` and `src/services/api.types.ts`. Keep new endpoint mappings there rather than adding ad hoc Axios calls to page components.

## Local development

### Requirements

- Node.js and npm
- A running Vortex backend, or another compatible API endpoint

From `frontend/`:

```bash
cp .env.example .env.local
npm install
npm run dev
```

Set `BACKEND_API_URL` in `.env.local`; the example uses `http://localhost:8000`. In Vercel, set `BACKEND_API_URL` in the project's environment variables. Open [http://localhost:3000](http://localhost:3000).

Available package scripts:

| Command | Purpose |
|---|---|
| `npm run dev` | Start the Next.js development server. |
| `npm run build` | Build the frontend for production. |
| `npm run start` | Serve a production build. |
| `npm run check` | Run Biome checks without writing changes. |
| `npm run format` | Format files under `src/`. |
| `npm run lint` | Run Biome checks and apply its safe fixes under `src/`. |

## Styling and responsive layout

The application uses Tailwind CSS utilities, shared UI components, and the existing dark visual theme. Dashboard content is centered within a fluid maximum width and adapts spacing and grids at larger breakpoints. Reuse the existing design tokens and components when extending the dashboard.

## Testing

**Status: Pending.** Test commands and results will be added after the frontend test workflow has been established and run.
