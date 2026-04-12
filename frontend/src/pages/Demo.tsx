import { Link } from "react-router-dom";
import type { Analytics } from "../types";
import MetricCard from "../components/MetricCard";
import EquityCurve from "../components/EquityCurve";
import TimeHeatmap from "../components/TimeHeatmap";
import BehaviorAlerts from "../components/BehaviorAlerts";
import Logo from "../components/Logo";
import MarketTicker from "../components/MarketTicker";
import LiveChart from "../components/LiveChart";

const DEMO_DATA: Analytics = {
  overview: {
    total_trades: 214,
    winners: 128,
    losers: 79,
    scratches: 7,
    win_rate: 59.8,
    gross_profit: 18420.5,
    gross_loss: 9870.25,
    average_winner: 143.91,
    average_loser: 124.94,
    largest_winner: 892.0,
    largest_loser: -645.0,
    profit_factor: 1.87,
    expectancy: 39.95,
    total_pnl: 8550.25,
    total_fees: 214.0,
    net_pnl: 8336.25,
    average_hold_time_minutes: 23,
    best_day: { date: "2025-11-14", pnl: 1245.0 },
    worst_day: { date: "2025-10-03", pnl: -872.5 },
  },
  time_analysis: {
    win_rate_by_hour: {
      "9": 72, "10": 64, "11": 55, "12": 48,
      "13": 52, "14": 61, "15": 58,
    },
    pnl_by_hour: {
      "9": 2180, "10": 1640, "11": 420, "12": -310,
      "13": 280, "14": 1890, "15": 950,
    },
    trades_by_hour: {
      "9": 48, "10": 42, "11": 30, "12": 18,
      "13": 22, "14": 32, "15": 22,
    },
    win_rate_by_day_of_week: {
      Monday: 54, Tuesday: 62, Wednesday: 65,
      Thursday: 58, Friday: 52,
    },
    pnl_by_day_of_week: {
      Monday: 820, Tuesday: 2150, Wednesday: 2680,
      Thursday: 1940, Friday: 960,
    },
    trades_by_day_of_week: {
      Monday: 42, Tuesday: 46, Wednesday: 44,
      Thursday: 48, Friday: 34,
    },
    best_hour: 9,
    worst_hour: 12,
    best_day: "Wednesday",
    worst_day: "Friday",
    win_rate_by_session: { "Pre-Market": 45, Regular: 61, "After-Hours": 38 },
    pnl_by_session: { "Pre-Market": -120, Regular: 8890, "After-Hours": -220 },
    trades_by_session: { "Pre-Market": 8, Regular: 198, "After-Hours": 8 },
  },
  behavioral: {
    revenge_trades: {
      alert: "12 revenge trades detected (5.6% of all trades). These trades have a 25% win rate and lost ₹1,240 total. Consider a 15-minute cooling-off period after losses.",
      count: 12,
      win_rate: 25,
      total_pnl: -1240,
      percentage_of_trades: 5.6,
      normal_win_rate: 59.8,
    },
    overtrading_days: {
      alert: "8 overtrading days identified where you exceeded 8 trades/day. Net P&L on those days: -₹620.",
      count: 8,
      total_pnl_on_overtrading_days: -620,
    },
    tilt_detection: {
      alert: null,
      tilt_events: 2,
      total_pnl_from_tilt: -380,
    },
    win_streak_behavior: {
      occurrences: 14,
      next_trade_win_rate: 52,
      next_trade_avg_pnl: 18.4,
      streak_threshold: 3,
    },
    loss_streak_behavior: {
      occurrences: 9,
      next_trade_win_rate: 44,
      next_trade_avg_pnl: -42.1,
      streak_threshold: 3,
    },
    monday_effect: {
      alert: "Your Monday win rate (54%) is below your average (59.8%). Consider a lighter size on Mondays.",
      is_significant: true,
      has_data: true,
    },
    friday_effect: { alert: null, is_significant: false, has_data: true },
    first_trade_of_day: {
      alert: "Your first trade of the day wins 68% of the time — significantly above average. Your patience pays off.",
      has_data: true,
    },
    last_trade_of_day: { alert: null, has_data: true },
    sizing_after_loss: { alert: null, has_data: true },
    time_between_trades: { alert: null, has_data: true },
  },
  symbols: {
    per_symbol: {
      SPY: { trades: 82, win_rate: 63.4, total_pnl: 3420, avg_pnl: 41.7, avg_hold_time: 18 },
      QQQ: { trades: 54, win_rate: 57.4, total_pnl: 2180, avg_pnl: 40.4, avg_hold_time: 22 },
      AAPL: { trades: 28, win_rate: 64.3, total_pnl: 1240, avg_pnl: 44.3, avg_hold_time: 31 },
      TSLA: { trades: 22, win_rate: 50.0, total_pnl: -180, avg_pnl: -8.2, avg_hold_time: 15 },
      NVDA: { trades: 18, win_rate: 61.1, total_pnl: 1420, avg_pnl: 78.9, avg_hold_time: 26 },
      AMD: { trades: 10, win_rate: 40.0, total_pnl: -530, avg_pnl: -53.0, avg_hold_time: 12 },
    },
    best_symbols: [
      { symbol: "NVDA", trades: 18, win_rate: 61.1, total_pnl: 1420, avg_pnl: 78.9, avg_hold_time: 26 },
      { symbol: "AAPL", trades: 28, win_rate: 64.3, total_pnl: 1240, avg_pnl: 44.3, avg_hold_time: 31 },
    ],
    worst_symbols: [
      { symbol: "AMD", trades: 10, win_rate: 40.0, total_pnl: -530, avg_pnl: -53.0, avg_hold_time: 12 },
      { symbol: "TSLA", trades: 22, win_rate: 50.0, total_pnl: -180, avg_pnl: -8.2, avg_hold_time: 15 },
    ],
    concentration_top3: 76.6,
  },
  streaks: {
    current_streak: { type: "win", count: 3 },
    max_win_streak: 8,
    max_loss_streak: 5,
    avg_win_streak: 3.2,
    avg_loss_streak: 2.1,
    streaks_history: [
      { type: "win", count: 8, pnl: 1120, start_date: "2025-11-10", end_date: "2025-11-14" },
      { type: "loss", count: 5, pnl: -640, start_date: "2025-10-01", end_date: "2025-10-03" },
      { type: "win", count: 6, pnl: 780, start_date: "2025-09-22", end_date: "2025-09-25" },
      { type: "loss", count: 4, pnl: -490, start_date: "2025-09-15", end_date: "2025-09-17" },
      { type: "win", count: 5, pnl: 620, start_date: "2025-09-08", end_date: "2025-09-11" },
    ],
  },
  equity_curve: {
    cumulative_pnl: generateEquityCurve(),
    drawdown_periods: [
      { start: "2025-10-01", end: "2025-10-08", depth: 1420 },
      { start: "2025-09-14", end: "2025-09-19", depth: 890 },
    ],
    max_drawdown: { amount: 1420, start: "2025-10-01", end: "2025-10-08" },
    rolling_win_rate_20: [],
    rolling_pnl_20: [],
  },
  risk_metrics: {
    average_risk_reward: 1.15,
    max_consecutive_losses: 5,
    average_daily_pnl: 98.24,
    std_daily_pnl: 245.6,
    trading_days: 87,
    sharpe_ratio: 1.42,
    sortino_ratio: 2.1,
    var_95: -380,
    calmar_ratio: 1.8,
  },
};

function generateEquityCurve() {
  // Seeded PRNG for deterministic demo data across renders
  let seed = 42;
  function seededRandom() {
    seed = (seed * 16807 + 0) % 2147483647;
    return (seed - 1) / 2147483646;
  }

  const points = [];
  let pnl = 0;
  const start = new Date("2025-08-01");
  for (let i = 0; i < 87; i++) {
    const date = new Date(start);
    date.setDate(date.getDate() + i);
    if (date.getDay() === 0 || date.getDay() === 6) continue;
    const dailyPnl = (seededRandom() - 0.38) * 300;
    pnl += dailyPnl;
    points.push({
      date: date.toISOString().split("T")[0],
      cumulative_pnl: Math.round(pnl * 100) / 100,
      trade_count: Math.floor(seededRandom() * 4) + 1,
    });
  }
  const finalTarget = 8550;
  const scale = finalTarget / (pnl || 1);
  return points.map((pt) => ({
    ...pt,
    cumulative_pnl: Math.round(pt.cumulative_pnl * scale * 100) / 100,
  }));
}

function formatPnl(value: number | null | undefined): string {
  if (value == null) return "—";
  const abs = Math.abs(value).toFixed(2);
  if (value > 0) return `+₹${abs}`;
  if (value < 0) return `-₹${abs}`;
  return `₹${abs}`;
}

function pnlArrow(value: number | null | undefined): string {
  if (value == null || value === 0) return "";
  return value > 0 ? " ▲" : " ▼";
}

export default function Demo() {
  const o = DEMO_DATA.overview;

  return (
    <div className="min-h-screen bg-bg-primary">
      <MarketTicker />
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm text-gray-400 hover:text-white transition-colors">
              Log in
            </Link>
            <Link to="/register" className="bg-accent text-bg-primary font-semibold text-sm px-5 py-2 rounded-lg hover:brightness-110 transition-all">
              Sign Up Free
            </Link>
          </div>
        </div>
      </nav>

      <div className="bg-accent/10 border-b border-accent/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p className="text-sm text-accent">
            <span className="font-semibold">Demo Mode</span> — You're viewing sample data from {o.total_trades} trades. Upload your own trades to see YOUR patterns.
          </p>
          <Link to="/register" className="text-sm font-semibold text-accent hover:text-white transition-colors whitespace-nowrap">
            Sign Up Free &rarr;
          </Link>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <MetricCard
            label="Total P&L"
            value={`${formatPnl(o.total_pnl)}${pnlArrow(o.total_pnl)}`}
            positive={o.total_pnl > 0}
            subValue={`${o.total_trades} trades`}
          />
          <MetricCard
            label="Win Rate"
            value={`${o.win_rate}%`}
            positive={o.win_rate >= 50}
            subValue={`${o.winners}W / ${o.losers}L`}
          />
          <MetricCard
            label="Profit Factor"
            value={o.profit_factor?.toFixed(2) ?? "—"}
            positive={o.profit_factor != null && o.profit_factor > 1}
          />
          <MetricCard
            label="Expectancy"
            value={`${formatPnl(o.expectancy)}${pnlArrow(o.expectancy)}`}
            positive={o.expectancy > 0}
            subValue="per trade"
          />
          <MetricCard
            label="Avg Winner"
            value={`+₹${o.average_winner.toFixed(2)} ▲`}
            positive={true}
          />
          <MetricCard
            label="Avg Loser"
            value={`-₹${o.average_loser.toFixed(2)} ▼`}
            positive={false}
          />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MetricCard
            label="Sharpe Ratio"
            value={DEMO_DATA.risk_metrics.sharpe_ratio?.toFixed(2) ?? "—"}
            positive={DEMO_DATA.risk_metrics.sharpe_ratio != null ? DEMO_DATA.risk_metrics.sharpe_ratio > 1 : null}
          />
          <MetricCard
            label="Risk/Reward"
            value={DEMO_DATA.risk_metrics.average_risk_reward?.toFixed(2) ?? "—"}
            positive={DEMO_DATA.risk_metrics.average_risk_reward != null && DEMO_DATA.risk_metrics.average_risk_reward > 1}
          />
          <MetricCard
            label="Best Day"
            value={`${formatPnl(o.best_day.pnl)}${pnlArrow(o.best_day.pnl)}`}
            positive={true}
            subValue={o.best_day.date}
          />
          <MetricCard
            label="Worst Day"
            value={`${formatPnl(o.worst_day.pnl)}${pnlArrow(o.worst_day.pnl)}`}
            positive={false}
            subValue={o.worst_day.date}
          />
        </div>

        {DEMO_DATA.equity_curve.cumulative_pnl.length > 0 && (
          <EquityCurve data={DEMO_DATA.equity_curve.cumulative_pnl} />
        )}

        <LiveChart symbol="NSE:NIFTY" height={620} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <BehaviorAlerts data={DEMO_DATA.behavioral} />
          </div>
          <div>
            <TimeHeatmap
              winRateByHour={DEMO_DATA.time_analysis.win_rate_by_hour}
              pnlByHour={DEMO_DATA.time_analysis.pnl_by_hour}
              winRateByDay={DEMO_DATA.time_analysis.win_rate_by_day_of_week}
              pnlByDay={DEMO_DATA.time_analysis.pnl_by_day_of_week}
            />
          </div>
        </div>

        <div className="bg-bg-card border border-accent/20 rounded-xl p-8 text-center">
          <h2 className="text-2xl font-bold text-white mb-2">Ready to analyze your own trades?</h2>
          <p className="text-gray-400 mb-6 max-w-lg mx-auto">
            Upload a CSV from any broker. TradeLoop detects revenge trades, overtrading, tilt, and 20+ behavioral patterns automatically.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 bg-accent text-bg-primary font-semibold text-base px-8 py-3.5 rounded-lg hover:brightness-110 transition-all"
          >
            Sign Up Free — It Takes 30 Seconds
          </Link>
          <p className="text-xs text-gray-500 mt-3">No credit card required</p>
        </div>
      </main>
    </div>
  );
}
