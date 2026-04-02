import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../store/auth";
import MetricCard from "../components/MetricCard";
import EquityCurve from "../components/EquityCurve";
import TimeHeatmap from "../components/TimeHeatmap";
import BehaviorAlerts from "../components/BehaviorAlerts";
import SymbolTable from "../components/SymbolTable";
import StreakDisplay from "../components/StreakDisplay";
import TradeTable from "../components/TradeTable";

interface Analytics {
  overview: any;
  time_analysis: any;
  behavioral: any;
  symbols: any;
  streaks: any;
  equity_curve: any;
  risk_metrics: any;
}

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"overview" | "behavior" | "time" | "symbols" | "trades">("overview");
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  useEffect(() => {
    api
      .get("/analytics/full")
      .then(({ data }) => setAnalytics(data))
      .catch((err) => setError(err.response?.data?.detail || "Failed to load analytics"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Crunching your trades...</p>
        </div>
      </div>
    );
  }

  const o = analytics?.overview;
  const isEmpty = !o || !o.total_trades;

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-7 h-7 bg-accent rounded-md flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0a0a0f" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
            </div>
            <span className="text-lg font-bold text-white">TradeLoop</span>
          </Link>

          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 hidden sm:block">{user?.email}</span>
            <Link to="/upload" className="btn-primary text-xs px-3 py-1.5">
              Upload Trades
            </Link>
            <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">
              Log out
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {isEmpty ? (
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
            {/* Tabs */}
            <div className="flex gap-1 mb-6 overflow-x-auto pb-2">
              {(
                [
                  ["overview", "Overview"],
                  ["behavior", "Behavioral"],
                  ["time", "Time Analysis"],
                  ["symbols", "Symbols"],
                  ["trades", "Trade Log"],
                ] as const
              ).map(([key, label]) => (
                <button
                  key={key}
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

            {error && (
              <div className="bg-loss/10 border border-loss/30 text-loss rounded-lg p-3 mb-6 text-sm">
                {error}
              </div>
            )}

            {activeTab === "overview" && (
              <div className="space-y-6">
                {/* Metric cards */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  <MetricCard
                    label="Total P&L"
                    value={`$${o.total_pnl?.toFixed(2)}`}
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
                    value={o.profit_factor === Infinity ? "∞" : o.profit_factor?.toFixed(2)}
                    positive={o.profit_factor > 1}
                  />
                  <MetricCard
                    label="Expectancy"
                    value={`$${o.expectancy?.toFixed(2)}`}
                    positive={o.expectancy > 0}
                    subValue="per trade"
                  />
                  <MetricCard
                    label="Avg Winner"
                    value={`$${o.average_winner?.toFixed(2)}`}
                    positive={true}
                  />
                  <MetricCard
                    label="Avg Loser"
                    value={`-$${o.average_loser?.toFixed(2)}`}
                    positive={false}
                  />
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <MetricCard
                    label="Largest Winner"
                    value={`$${o.largest_winner?.toFixed(2)}`}
                    positive={true}
                  />
                  <MetricCard
                    label="Largest Loser"
                    value={`$${o.largest_loser?.toFixed(2)}`}
                    positive={false}
                  />
                  <MetricCard
                    label="Best Day"
                    value={`$${o.best_day?.pnl?.toFixed(2)}`}
                    positive={true}
                    subValue={o.best_day?.date}
                  />
                  <MetricCard
                    label="Worst Day"
                    value={`$${o.worst_day?.pnl?.toFixed(2)}`}
                    positive={false}
                    subValue={o.worst_day?.date}
                  />
                </div>

                {/* Equity curve */}
                {analytics?.equity_curve?.cumulative_pnl && (
                  <EquityCurve data={analytics.equity_curve.cumulative_pnl} />
                )}

                {/* Risk metrics */}
                {analytics?.risk_metrics && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <MetricCard
                      label="Sharpe Ratio"
                      value={analytics.risk_metrics.sharpe_ratio ?? "—"}
                      positive={analytics.risk_metrics.sharpe_ratio ? analytics.risk_metrics.sharpe_ratio > 1 : null}
                    />
                    <MetricCard
                      label="Risk/Reward"
                      value={analytics.risk_metrics.average_risk_reward ?? "—"}
                      positive={analytics.risk_metrics.average_risk_reward > 1}
                    />
                    <MetricCard
                      label="Max Consec. Losses"
                      value={analytics.risk_metrics.max_consecutive_losses ?? "—"}
                      positive={false}
                    />
                    <MetricCard
                      label="Daily P&L Std"
                      value={`$${analytics.risk_metrics.std_daily_pnl?.toFixed(2) ?? "—"}`}
                    />
                  </div>
                )}

                {/* Streaks */}
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
          </>
        )}
      </div>
    </div>
  );
}
