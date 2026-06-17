# SentinelIQ

AI-powered corporate fraud early warning platform for equity analysts, independent investors, and risk professionals. Enter a ticker; SentinelIQ runs five independent forensic analyses and produces a **Corporate Integrity Score (0–100)** plus an analyst-style report.

**What it analyzes:** public financial statements (via Yahoo Finance) and news headlines (via RSS). It does **not** analyze SEC filings, earnings call transcripts, or insider transaction data — see [`docs/data-sources.md`](docs/data-sources.md) for the honest breakdown.

---

## Architecture

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 App Router, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python 3.11+), async SQLAlchemy |
| Database | PostgreSQL (Alembic migrations) |
| AI | Google Gemini 2.5 Flash (`temperature=0`, pinned model ID) |
| Finance data | yfinance (Yahoo Finance) |
| News | feedparser over Google News / Yahoo Finance / Reuters RSS |
| Auth | JWT + bcrypt |
| Hosting | Vercel (frontend) + Render free tier (backend + DB) |

---

## Development Setup

**Prerequisites:** Python 3.11+, Node 18+, PostgreSQL running locally or a Neon/Supabase connection string.

```bash
# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate   # Windows
# source .venv/bin/activate                       # macOS/Linux
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, GEMINI_API_KEY, SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

The backend API is at `http://localhost:8000`. The OpenAPI docs are at `http://localhost:8000/docs`.

---

## Documentation

| Doc | Contents |
|---|---|
| [`docs/data-sources.md`](docs/data-sources.md) | Exactly where every input comes from and what that means for the fraud-detection claims |
| [`docs/scoring-methodology.md`](docs/scoring-methodology.md) | All five forensic algorithms and the weight formula |
| [`docs/architecture.md`](docs/architecture.md) | System design, key ADRs, component map |
| [`docs/api-reference.md`](docs/api-reference.md) | All REST endpoints with request/response shapes |
| [`docs/deployment.md`](docs/deployment.md) | Render + Vercel deployment playbook |
| `CLAUDE.md` | Full project constitution (algorithms, design system, decisions) |

---

## Scoring

The Corporate Integrity Score is a weighted average of five forensic modules:

| Module | Weight | Signal source |
|---|---|---|
| Revenue Quality | 33.3% | yfinance financials |
| Cash Flow Integrity | 22.2% | yfinance financials |
| Governance | 16.7% | News headlines → Gemini |
| Earnings Quality | 16.7% | yfinance financials |
| News Tone | 11.1% | RSS sentiment |

Narrative Consistency is computed and displayed but carries **zero weight** until a real transcript pipeline exists (Horizon 2 — see `FUTURE_ARCHITECTURE.md`).

**0–20 Severe risk · 21–40 High · 41–60 Moderate · 61–80 Low · 81–100 Strong integrity**
