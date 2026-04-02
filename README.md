# TradeLoop

Trade journal analytics engine for day traders and prop firm traders.

Upload your trade history. TradeLoop finds the patterns you can't see — revenge trades, best hours, worst setups, behavioral leaks — so you stop losing money to yourself.

## Quick Start

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your PostgreSQL connection string

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

### Sample Data

A `sample_trades.csv` with 200 realistic trades is included. Upload it after registering to see the full dashboard immediately.

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy 2 + asyncpg, PostgreSQL
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Recharts
- **Auth**: JWT with bcrypt
- **Deployment**: Docker (Railway) + Vercel

## Analytics Engine

The core product — a deterministic math engine that computes 50+ metrics from trade data:

- **Performance**: Win rate, profit factor, expectancy, risk/reward
- **Time Analysis**: P&L by hour, day of week, trading session
- **Behavioral Patterns**: Revenge trading, tilt detection, overtrading, streak behavior
- **Symbol Analysis**: Per-instrument performance breakdown
- **Risk Metrics**: Sharpe ratio, Sortino ratio, VaR, max drawdown
- **Equity Curve**: Cumulative P&L, drawdown periods, rolling metrics

No LLM. No external APIs. Pure math. Every number is correct.
