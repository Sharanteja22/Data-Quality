# Data Quality Backend

Existing Spring Boot backend plus a separate JWT authentication module.

## Authentication module

### 1. Create the USERS table
Run `database/auth_setup.sql` in the existing `TEJA_DATA_QUALITY_DB.DQ` Snowflake schema. This adds one table; it does not modify the six existing DQ tables.

### 2. Configure JWT secret
For local development, a development-only fallback secret is configured. Before sharing or deploying the application, set a private Base64-encoded secret of at least 256 bits:

PowerShell:
```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$env:JWT_SECRET = [Convert]::ToBase64String($bytes)
```
Keep this value private. Do not commit it to GitHub. JWT lifetime is 1 hour by default.

Optional bootstrap admin:
```powershell
$env:BOOTSTRAP_ADMIN_EMAIL = "admin@example.com"
```
If set, only that email receives ADMIN at registration. Otherwise, the first registered account becomes ADMIN and subsequent registrations become OPERATOR. First-user bootstrap is synchronized within one backend instance; for multi-instance deployment, pre-provision the admin.

### 3. Start backend
```powershell
.\mvnw.cmd spring-boot:run
```

### 4. Auth endpoints
- `POST /api/auth/register` with `{ "fullName": "Admin User", "email": "admin@example.com", "password": "StrongPassword123" }`
- `POST /api/auth/login` with `{ "email": "admin@example.com", "password": "StrongPassword123" }`
- `GET /api/auth/me` with `Authorization: Bearer <accessToken>`

Successful login/register returns `accessToken`, `tokenType`, `expiresIn`, and `user` (`userId`, `fullName`, `email`, `role`).

### 5. Existing APIs are protected
All application APIs other than `/api/auth/login`, `/api/auth/register`, `/api/health`, and `/api/health/snowflake` now require a valid Bearer token. Send the token with batch, run, exception, replay, and publication API requests.

Role names: `ADMIN`, `OPERATOR`, `ANALYST`, `STEWARD`. Registration never accepts a role from the browser. The first account is ADMIN by default; later accounts are OPERATOR. For this initial iteration, role changes can be provisioned in Snowflake:
```sql
UPDATE USERS SET USER_ROLE = 'ANALYST' WHERE EMAIL = 'analyst@example.com';
```
The next login will issue a token with the updated role.

## Human-readable references

- New batch IDs use `BAT-YYYYMMDD-XXXXX` (the internal batch key remains the same value).
- Existing historical `BATCH-...` values remain valid; API responses expose `DISPLAY_BATCH_ID` as a readable `BAT-...` alias.
- Exception UUIDs remain unchanged for database relationships and API updates. The exception list response also exposes `DISPLAY_EXCEPTION_ID`, formatted as `EXC-` plus 12 UUID hex characters. Use this display reference in the UI; use `EXCEPTION_ID` internally for PATCH requests.

### Initial API role permissions
- ADMIN: all authenticated application APIs.
- OPERATOR: upload and replay, plus read APIs.
- ANALYST: read APIs only.
- STEWARD: read APIs and update exceptions.
