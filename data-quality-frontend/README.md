# Data Quality Frontend — Authenticated UI

Responsive React + Vite application for the Operational Data Quality Scorecard.

## Stack
React 18, Vite, Tailwind CSS 3, shadcn/ui-inspired local primitives, Lucide, Recharts, Axios, React Router.

## Run
Requirements: Node.js 20+.
```powershell
npm install
Copy-Item .env.example .env
npm run dev
```
Open http://localhost:5173. Run Spring Boot separately on port 8080.

Vite proxies `/api` to `http://localhost:8080`.

## Authentication contract
- `POST /api/auth/login` body `{ "email": "...", "password": "..." }`
- `POST /api/auth/register` body `{ "fullName": "...", "email": "...", "password": "..." }`
- `GET /api/auth/me` with `Authorization: Bearer <accessToken>`
- Login/register response contains `accessToken`, `tokenType`, `expiresIn`, and `user` (`userId`, `fullName`, `email`, `role`).
- Current-user response contains `user_id`, `full_name`, `email`, `role`.

The frontend stores the JWT in sessionStorage for this initial local application. The backend remains responsible for authorization. Role-aware navigation is only a user-experience layer.

## Role navigation
- ADMIN: all available pages
- OPERATOR: overview, batches, upload
- ANALYST: overview, batches
- STEWARD: overview, batches, exceptions

## Important
The frontend does not implement DQ rules or publication decisions. Those remain in Spring Boot/Python. It never connects directly to Snowflake or AWS. Demo chart trends are marked illustrative until analytical APIs/views are connected.


## Batch scorecard and exception management
- Open a batch from the Batches table to view batch metadata and processing run history.
- Select a run to load its scorecard, five dimension scores, rule results, publication eligibility, and exceptions.
- Exception management supports search/filtering and editing status, assigned team, and resolution notes.
- The UI reads the backend response envelopes used by the API (`batch` + `runs`, and `value` + `Count`).
