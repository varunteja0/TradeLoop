# TradeLoop

**Stop losing money to yourself.**

TradeLoop is a trading behavior engine that computes the exact dollar cost of every mistake you make — and tells you how to fix it. Not a journal. Not a charting tool. A behavior engine.

## What Makes It Different

Other tools say "you revenge traded 12 times." TradeLoop says:

> "Revenge trading cost you exactly $4,873. Here's your equity curve without those trades. If you stop, you save $1,600/month."

No other trading analytics product does this.

## Features

| Feature | What It Does |
|---------|-------------|
| **Counterfactual Insights** | Exact dollar cost of every behavioral leak: revenge trading, bad hours, overtrading, tilt sizing |
| **Trade Replay** | Click any trade, see it on a real historical price chart with entry/exit markers, MFE/MAE |
| **Prop Firm Compliance** | Real-time drawdown tracking for FTMO, FundingPips, The5ers, TopStep, MyForexFunds |
| **Live Market Data** | TradingView ticker + charts + portfolio panel with real-time prices |
| **Emotion Tracking** | Tag trades with your mood. See: "When you trade from FOMO, your win rate drops to 23%." |
| **Weekly Intelligence** | Graded weekly report (A-F) with top insights and specific action items |
| **Broker Auto-Sync** | Zerodha Kite Connect + Angel One SmartAPI (architecture ready, needs API keys) |
| **50+ Analytics Metrics** | Win rate, profit factor, Sharpe, Sortino, Calmar, expectancy, streaks, time analysis |

## Quick Start

```bash
# Backend
cd /path/to/TradeLoop
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. No database setup needed — SQLite auto-creates on first start.

### Demo Account

After starting, create a demo account with sample data:

```bash
# Register
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@tradeloop.io","password":"Trade123","name":"Demo Trader"}'

# Upload sample trades (200 realistic trades included)
TOKEN=<token from register response>
curl -s -X POST "http://localhost:8000/api/v1/trades/upload?broker=auto" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_trades.csv"
```

Or visit **http://localhost:5173/demo** for an instant preview without registration.

## Architecture

```
API Layer (thin routes)
    ↓
Service Layer (business logic + event emission)
    ↓
Engine Layer (pure computation, zero I/O)
    ↓
Infrastructure (event bus, cache, DB)
```

- **Modular monolith** with enforced domain boundaries
- **Event-driven** — trade.uploaded triggers cache invalidation, compliance check, background precompute
- **In-memory cache** with TTL — analytics return in sub-10ms on cache hit
- **API versioned** at /api/v1/ with request IDs and structured errors
- **60 automated tests** (47 backend + 13 frontend)
- **CI/CD** via GitHub Actions (lint + type-check + test + build)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9+, FastAPI, SQLAlchemy 2, asyncpg/aiosqlite |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Charts | TradingView Widgets (live), Lightweight Charts (replay) |
| Auth | JWT (access + refresh), bcrypt, Fernet-encrypted secrets |
| Payments | Razorpay (3 tiers: free/pro/prop_trader) |
| CI/CD | GitHub Actions, Docker, Railway + Vercel ready |

## API Endpoints

All routes available at `/api/v1/` (and `/api/` for backward compat).

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Create account |
| POST | /auth/login | Login, get tokens |
| POST | /auth/refresh | Refresh access token |
| GET | /auth/me | Current user |
| POST | /trades/upload | Upload CSV trades |
| GET | /trades | List trades (paginated, filterable, sortable) |
| PATCH | /trades/{id} | Update trade (mood, notes) |
| GET | /analytics/full | Complete analytics (cached) |
| GET | /analytics/emotions | Mood-performance correlation |
| GET | /insights/full | Counterfactual dollar-value analysis |
| GET | /market/replay/{trade_id} | Trade replay with MFE/MAE |
| GET | /prop | List prop accounts |
| POST | /prop | Create prop account |
| GET | /prop/{id}/compliance | Real-time compliance check |
| GET | /reports/weekly | Weekly intelligence report |
| GET | /broker/connections | List broker connections |
| POST | /payments/create-order | Start subscription |

## Project Structure

```
TradeLoop/
├── app/
│   ├── api/          # Thin route handlers (9 files)
│   ├── services/     # Business logic + events (7 files)
│   ├── engine/       # Pure computation (8 files)
│   ├── models/       # SQLAlchemy models (4 files)
│   ├── schemas/      # Pydantic validation
│   ├── main.py       # FastAPI app + middleware
│   ├── crypto.py     # Fernet encryption for secrets
│   └── security.py   # JWT + bcrypt
├── frontend/
│   ├── src/
│   │   ├── pages/        # 14 pages
│   │   ├── components/   # 15 components
│   │   ├── lib/          # React Query setup
│   │   └── store/        # Zustand auth store
│   └── vitest.config.ts
├── tests/            # 47 backend tests
├── sample_trades.csv # 200 realistic trades
├── STRATEGY.md       # Product strategy document
└── docker-compose.yml
```

## License

Proprietary. All rights reserved.
