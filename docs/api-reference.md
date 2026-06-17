# API Reference

All routes are mounted under `/api/v1` except `/health`.

**Base URL (local):** `http://localhost:8000`  
**Authentication:** `Authorization: Bearer <JWT>` on all `/api/v1/` routes except `/auth/register`, `/auth/login`, and `/health`.

---

## Health

### `GET /health`
DB connectivity probe. No auth required. Used by Render to detect free-tier spin-downs.

```json
{ "status": "ok", "database": "ok" }
```

---

## Auth

### `POST /api/v1/auth/register`
Create a new user account.

**Body:** `{ "email": str, "password": str, "full_name": str }`  
**Returns:** `{ "access_token": str, "token_type": "bearer" }`

### `POST /api/v1/auth/login`
OAuth2 password form login.

**Body (form):** `username=<email>&password=<password>`  
**Returns:** `{ "access_token": str, "token_type": "bearer" }`

### `GET /api/v1/auth/me`
Current user profile.

**Returns:** `{ "id", "email", "full_name", "tier", "created_at" }`

---

## Company

### `GET /api/v1/company/search?q=<query>`
Case-insensitive search by name or ticker. Returns up to 10 results.

### `GET /api/v1/company/{ticker}`
Fetch company metadata. Creates the company record (via yfinance) if it doesn't exist yet.

**Returns:** `{ "id", "name", "ticker", "sector", "exchange", "last_analyzed" }`  
**Errors:** `404` if the ticker is unknown to yfinance.

---

## Analysis

### `POST /api/v1/analysis/run`
Trigger a full analysis for a company. The company must exist first (call `GET /company/{ticker}`).

**Body:** `{ "ticker": str }`  
**Returns:** `{ "analysis_id": uuid, "status": "pending" | "complete" }` — `"complete"` means a cached result within the 6-hour TTL was returned.  
**Errors:** `403 LIMIT_REACHED` if the free-tier monthly quota (5 fresh analyses) is exhausted; `404` if the company doesn't exist.

### `GET /api/v1/analysis/{analysis_id}/status`
Poll during a running analysis.

**Returns:** `{ "status": str, "stage": str, "elapsed_seconds": int }`  
Status values: `"pending"` → `"running"` → `"complete"` | `"error"`.

### `GET /api/v1/analysis/company/{ticker}`
Latest completed analysis for a company, including all module scores and red flags.

**Returns:** Full `AnalysisResultResponse` with `integrity_score`, 6 module scores, `module_details` (JSON blob with forensic details and AI provenance), and `red_flags[]`.

### `GET /api/v1/analysis/company/{ticker}/history`
Score history for the trend chart. Up to 24 completed analyses, oldest first.

**Returns:** `[{ "id", "run_at", "integrity_score", "financial_score", "cashflow_score", "governance_score", "earnings_score", "narrative_score", "news_score" }, ...]`  
**Errors:** `404` if ticker doesn't exist; `[]` (200) if no completed analyses yet.

---

## Report

### `GET /api/v1/report/company/{ticker}`
AI-generated analyst report (Markdown) for the latest analysis.

**Returns:** `{ "content": str (Markdown), "generated_at": datetime }`

---

## Watchlist

### `GET /api/v1/watchlist`
Current user's watchlist with the latest integrity score per company.

### `POST /api/v1/watchlist`
Add a company to the watchlist.

**Body:** `{ "ticker": str }`  
**Errors:** `409` if the company is already on the watchlist.

### `DELETE /api/v1/watchlist/{ticker}`
Remove a company from the watchlist.

---

## Error envelope

All errors use the same shape:

```json
{ "error": { "code": "STRING_CODE", "message": "Human-readable description" } }
```

Common codes: `NOT_FOUND`, `LIMIT_REACHED`, `UNAUTHORIZED`, `VALIDATION_ERROR`.
