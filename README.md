# SentinelIQ

SentinelIQ is an institutional-grade financial forensics engine designed to analyze public company filings, transcripts, and financial data to detect potential fraud, inconsistencies, and governance risks. Built for investors, equity analysts, and risk professionals.

## Architecture

SentinelIQ is built on a modern, decoupled architecture:
- **Frontend**: Next.js 14 App Router, React, Tailwind CSS. Features a custom component library built with an institutional aesthetic (warm canvas backgrounds, editorial typography, and rigid monospaced data).
- **Backend**: FastAPI Python Server running forensic risk models and NLP capabilities.
- **Database**: PostgreSQL schemas and migrations for robust data storage.
- **AI Integration**: Gemini API for analyst-style report generation.

## Project Structure

```text
sentineliq/
├── frontend/                        # Next.js 14 App Router
│   ├── app/                         # Marketing, Dashboard, and Analysis views
│   ├── components/                  # Custom design system (ScoreCards, RedFlagTimelines, etc.)
│   └── ...
├── backend/                         # FastAPI Python Server
│   ├── core/                        # Forensics, narrative, governance modules
│   └── ...
├── database/                        # SQL Schemas & Migrations
├── docs/                            # Technical Documentation
└── scripts/                         # Dev & Deployment Scripts
```

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sohan1611/SentinelIQ.git
   cd SentinelIQ
   ```

2. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your keys (specifically `GEMINI_API_KEY`).

3. **Run via Docker**:
   ```bash
   docker-compose up -d
   ```
   *The application will be available at `http://localhost:3000`.*

4. **Run Frontend Locally**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   *Navigate to `http://localhost:3000/design-system` to view the UI component library reference sheet.*

## Documentation

See the `docs/` directory for detailed architecture, methodology, and API reference.
