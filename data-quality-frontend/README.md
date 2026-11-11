# Data Quality Frontend

Responsive React + Vite frontend starter for the Operational Data Quality Scorecard.

## Stack
- React 18 + Vite
- Tailwind CSS 3
- shadcn/ui-inspired local primitives (Button, Card, Badge, Input)
- Lucide icons
- Recharts
- Axios + React Router

The components are intentionally lightweight and locally owned. They follow the shadcn/ui composition style without adding a large component framework.

## Run locally

Requirements: Node.js 20+ and npm.

```bash
npm install
cp .env.example .env
npm run dev
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Open http://localhost:5173.

The Vite development server proxies `/api` requests to `http://localhost:8080`. Start the Spring Boot backend separately.

## Backend endpoints used

- `GET /api/health`
- `GET /api/batches`
- `GET /api/batches/{batchId}`
- `POST /api/batches/upload` (multipart field: `file`)
- `GET /api/runs/{runId}/scorecard`
- `GET /api/runs/{runId}/rule-results`
- `GET /api/runs/{runId}/exceptions`
- `PATCH /api/exceptions/{exceptionId}`

The dashboard and batch list attempt to load live API data. If the backend is unavailable or returns a different response shape, the UI shows a clear connection/error state and uses sample dashboard values only for the visual overview. Upload requires the backend to be running.

## Project structure

```text
src/
  api/                 Axios client and API functions
  components/
    layout/            Sidebar, top bar, app shell
    ui/                Small shadcn-style primitives
  data/                Dashboard sample data
  pages/               Dashboard, batches, upload, exceptions
  App.jsx
  index.css
  main.jsx
```

## Theme

- Primary: Deep navy `#1E3A8A`
- Surfaces: `#F8FAFC`, `#E2E8F0`
- Accent: Electric blue `#3B82F6`

## Notes

This is a frontend starter, not a replacement for backend validation or publication controls. All data-quality decisions must remain in Spring Boot/Python. Do not put Snowflake or AWS credentials in the frontend. The browser should call Spring Boot APIs only.
