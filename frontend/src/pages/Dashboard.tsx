import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../store/auth";
import { useToast } from "../components/Toast";
import Logo from "../components/Logo";
import type { Analytics } from "../types";
import MetricCard from "../components/MetricCard";
import EquityCurve from "../components/EquityCurve";
import TimeHeatmap from "../components/TimeHeatmap";
import BehaviorAlerts from "../components/BehaviorAlerts";
import SymbolTable from "../components/SymbolTable";
import StreakDisplay from "../components/StreakDisplay";
import TradeTable from "../components/TradeTable";

type TabKey = "overview" | "behavior" | "time" | "symbols" | "trades";

const TAB_LABELS: Record<TabKey, string> = {
  overview: "Overview",
  behavior: "Behavioral",
  time: "Time Analysis",
  symbols: "Symbols",
  trades: "Trade Log",
};

type DateRange = "all" | "week" | "month" | "30d" | "90d";

const DATE_RANGE_OPTIONS: { value: DateRange; label: string }[] = [
  { value: "all", label: "All Time" },
  { value: "week", label: "This Week" },
  { value: "month", label: "This Month" },
  { value: "30d", label: "Last 30 Days" },
  { value: "90d", label: "Last 90 Days" },
];

function getDateRangeBounds(range: DateRange): { from: Date | null; to: Date } {
  const now = new Date();
  const to = now;
  if (range === "all") return { from: null, to };

  const from = new Date(now);
  switch (range) {
    case "week": {
      const day = from.getDay();
      from.setDate(from.getDate() - (day === 0 ? 6 : day - 1));
      break;
    }
    case "month":
      from.setDate(1);
      break;
    case "30d":
      from.setDate(from.getDate() - 30);
      break;
    case "90d":
      from.setDate(from.getDate() - 90);
      break;
  }
  from.setHours(0, 0, 0, 0);
  return { from, to };
}

function formatPnl(value: number | null | undefined): string {
  if (value == null) return "—";
  const abs = Math.abs(value).toFixed(2);
  if (value > 0) return `+$${abs}`;
  if (value < 0) return `-$${abs}`;
  return `$${abs}`;
}

function pnlArrow(value: number | null | undefined): string {
  if (value == null || value === 0) return "";
  return value > 0 ? " ▲" : " ▼";
}

function SkeletonCard() {
  return (
    <div className="card animate-pulse">
      <div className="h-4 bg-bg-hover rounded w-1/2 mb-3" />
      <div className="h-8 bg-bg-hover rounded w-3/4" />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [dateRange, setDateRange] = useState<DateRange>("all");
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const { toast } = useToast();

  useEffect(() => {
    document.title = `${TAB_LABELS[activeTab]} — TradeLoop Dashboard`;
  }, [activeTab]);

  useEffect(() => {
    api
      .get("/analytics/full")
      .then(({ data }) => setAnalytics(data))
      .catch((err: unknown) => {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          "Failed to load analytics";
        toast(msg, "error");
      })
      .finally(() => setLoading(false));
  }, [toast]);

  const filteredEquityCurve = useMemo(() => {
    if (!analytics?.equity_curve?.cumulative_pnl || dateRange === "all") {
      return analytics?.equity_curve?.cumulative_pnl ?? [];
    }
    const { from } = getDateRangeBounds(dateRange);
    if (!from) return analytics.equity_curve.cumulative_pnl;
    return analytics.equity_curve.cumulative_pnl.filter(
      (pt) => new Date(pt.date) >= from
    );
  }, [analytics, dateRange]);

  const o = analytics?.overview;
  const isEmpty = !o || !o.total_trades;

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />

          <div className="flex items-center gap-2 sm:gap-3">
            <Link to="/insights" className="text-xs text-accent hover:text-accent/80 font-medium hidden sm:block" title="Dollar-value leak analysis">
              Insights
            </Link>
            <Link to="/prop" className="text-xs text-gray-400 hover:text-white hidden sm:block">
              Prop Firm
            </Link>
            <Link to="/report" className="text-xs text-gray-400 hover:text-white hidden sm:block">
              Weekly Report
            </Link>
            <Link to="/connect" className="text-xs text-gray-400 hover:text-white hidden sm:block">
              Brokers
            </Link>
            <Link to="/upload" className="btn-primary text-xs px-3 py-1.5">
              Upload
            </Link>
            <Link to="/settings" className="text-xs text-gray-500 hover:text-gray-300 transition-colors hidden sm:block">
              Settings
            </Link>
            <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {loading ? (
          <DashboardSkeleton />
        ) : isEmpty ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-20">📊</div>
            <h2 className="text-2xl font-bold text-white mb-2">No trades yet</h2>
            <p className="text-gray-400 mb-6">Upload your first CSV to see your analytics dashboard.</p>
            <Link to="/upload" className="btn-primary">
              Upload Trades
            </Link>
          </div>
        ) : (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
              <div
                className="flex gap-1 overflow-x-auto pb-2 sm:pb-0"
                role="tablist"
                aria-label="Dashboard sections"
              >
                {(Object.entries(TAB_LABELS) as [TabKey, string][]).map(([key, label]) => (
                  <button
                    key={key}
                    role="tab"
                    id={`tab-${key}`}
                    aria-selected={activeTab === key}
                    aria-controls={`panel-${key}`}
                    onClick={() => setActiveTab(key)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                      activeTab === key
                        ? "bg-accent text-bg-primary"
                        : "text-gray-400 hover:text-white hover:bg-bg-hover"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div>
                <label htmlFor="date-range" className="sr-only">
                  Date range
                </label>
                <select
                  id="date-range"
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value as DateRange)}
                  className="input-field text-sm py-1.5 px-3 bg-bg-card border border-border rounded-lg text-gray-300"
                >
                  {DATE_RANGE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div
              role="tabpanel"
              id={`panel-${activeTab}`}
              aria-labelledby={`tab-${activeTab}`}
            >
              {activeTab === "overview" && (
                <div className="space-y-6">
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
                      value={o.profit_factor === Infinity ? "∞" : o.profit_factor?.toFixed(2) ?? "—"}
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
                      value={`+$${o.average_winner?.toFixed(2)} ▲`}
                      positive={true}
                    />
                    <MetricCard
                      label="Avg Loser"
                      value={`-$${o.average_loser?.toFixed(2)} ▼`}
                      positive={false}
                    />
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <MetricCard
                      label="Largest Winner"
                      value={`+$${o.largest_winner?.toFixed(2)} ▲`}
                      positive={true}
                    />
                    <MetricCard
                      label="Largest Loser"
                      value={`-$${Math.abs(o.largest_loser)?.toFixed(2)} ▼`}
                      positive={false}
                    />
                    <MetricCard
                      label="Best Day"
                      value={`${formatPnl(o.best_day?.pnl)}${pnlArrow(o.best_day?.pnl)}`}
                      positive={true}
                      subValue={o.best_day?.date}
                    />
                    <MetricCard
                      label="Worst Day"
                      value={`${formatPnl(o.worst_day?.pnl)}${pnlArrow(o.worst_day?.pnl)}`}
                      positive={false}
                      subValue={o.worst_day?.date}
                    />
                  </div>

                  {filteredEquityCurve.length > 0 && (
                    <EquityCurve data={filteredEquityCurve} />
                  )}

                  {analytics?.risk_metrics && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <MetricCard
                        label="Sharpe Ratio"
                        value={analytics.risk_metrics.sharpe_ratio?.toFixed(2) ?? "—"}
                        positive={
                          analytics.risk_metrics.sharpe_ratio != null
                            ? analytics.risk_metrics.sharpe_ratio > 1
                            : null
                        }
                      />
                      <MetricCard
                        label="Risk/Reward"
                        value={analytics.risk_metrics.average_risk_reward?.toFixed(2) ?? "—"}
                        positive={
                          analytics.risk_metrics.average_risk_reward != null &&
                          analytics.risk_metrics.average_risk_reward > 1
                        }
                      />
                      <MetricCard
                        label="Max Consec. Losses"
                        value={analytics.risk_metrics.max_consecutive_losses ?? "—"}
                        positive={false}
                      />
                      <MetricCard
                        label="Daily P&L Std"
                        value={
                          analytics.risk_metrics.std_daily_pnl != null
                            ? `$${analytics.risk_metrics.std_daily_pnl.toFixed(2)}`
                            : "—"
                        }
                      />
                    </div>
                  )}

                  {analytics?.streaks && <StreakDisplay data={analytics.streaks} />}
                </div>
              )}

              {activeTab === "behavior" && analytics?.behavioral && (
                <BehaviorAlerts data={analytics.behavioral} />
              )}

              {activeTab === "time" && analytics?.time_analysis && (
                <TimeHeatmap
                  winRateByHour={analytics.time_analysis.win_rate_by_hour || {}}
                  pnlByHour={analytics.time_analysis.pnl_by_hour || {}}
                  winRateByDay={analytics.time_analysis.win_rate_by_day_of_week || {}}
                  pnlByDay={analytics.time_analysis.pnl_by_day_of_week || {}}
                />
              )}

              {activeTab === "symbols" && analytics?.symbols?.per_symbol && (
                <SymbolTable perSymbol={analytics.symbols.per_symbol} />
              )}

              {activeTab === "trades" && <TradeTable />}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
