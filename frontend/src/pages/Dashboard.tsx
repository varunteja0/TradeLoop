import { useState, useEffect, useMemo, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../store/auth";
import { useToast } from "../components/Toast";
import Logo from "../components/Logo";
import { Modal } from "../components/ui";
import type { Analytics } from "../types";
import MetricCard from "../components/MetricCard";
import EquityCurve from "../components/EquityCurve";
import TimeHeatmap from "../components/TimeHeatmap";
import BehaviorAlerts from "../components/BehaviorAlerts";
import SymbolTable from "../components/SymbolTable";
import StreakDisplay from "../components/StreakDisplay";
import TradeTable from "../components/TradeTable";
import TradeChart from "../components/TradeChart";
import MarketTicker from "../components/MarketTicker";
import LiveChart from "../components/LiveChart";

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
  if (value > 0) return `+₹${abs}`;
  if (value < 0) return `-₹${abs}`;
  return `₹${abs}`;
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

function SidebarLink({ to, icon, label, active, accent }: { to: string; icon: string; label: string; active?: boolean; accent?: boolean }) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
        active ? "bg-accent/10 text-accent font-medium" : accent ? "text-accent hover:bg-bg-hover" : "text-gray-400 hover:text-white hover:bg-bg-hover"
      }`}
    >
      <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d={icon} />
      </svg>
      <span>{label}</span>
    </Link>
  );
}

function EmptyDashboard({ onSampleLoaded }: { onSampleLoaded: () => void }) {
  const [loadingSample, setLoadingSample] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const registeredAt = localStorage.getItem("tradeloop_registered_at");
    if (registeredAt && Date.now() - parseInt(registeredAt) < 5 * 60 * 1000) {
      setShowModal(true);
      localStorage.removeItem("tradeloop_registered_at");
    }
  }, []);

  const handleLoadSample = async () => {
    setLoadingSample(true);
    setShowModal(false);
    try {
      const { data } = await api.post("/trades/load-sample");
      toast(`${data.imported} sample trades loaded!`, "success");
      onSampleLoaded();
    } catch (err: any) {
      toast(err.response?.data?.detail || "Failed to load sample data", "error");
    } finally {
      setLoadingSample(false);
    }
  };

  return (
    <>
      <Modal open={showModal} onClose={() => setShowModal(false)} title="Welcome to TradeLoop">
        <p className="text-gray-400 text-sm mb-6">
          Upload your trade history to see your patterns — or explore with sample data first.
        </p>
        <div className="space-y-3">
          <button onClick={() => { setShowModal(false); navigate("/upload"); }}
            className="btn-primary w-full text-sm py-3">
            Upload My Trades
          </button>
          <button onClick={handleLoadSample} disabled={loadingSample}
            className="btn-secondary w-full text-sm py-3">
            {loadingSample ? "Loading sample data..." : "Try With Sample Data"}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-4 text-center">
          Sample data shows 200 realistic trades so you can explore every feature.
        </p>
      </Modal>

      <div className="text-center py-16">
        <div className="max-w-md mx-auto">
          <h2 className="text-2xl font-bold text-white mb-3">Your dashboard is ready. Let's fill it.</h2>
          <p className="text-gray-400 mb-8 text-sm">
            Upload your trade history to see your patterns, or try sample data to explore what TradeLoop can do.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/upload" className="btn-primary px-6 py-3 text-sm">
              Upload My Trades
            </Link>
            <button onClick={handleLoadSample} disabled={loadingSample}
              className="btn-secondary px-6 py-3 text-sm">
              {loadingSample ? "Loading..." : "Try With Sample Data"}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-6">
            The sample data shows real analytics so you can see what TradeLoop does before uploading your own trades.
          </p>
        </div>
      </div>
    </>
  );
}

export default function Dashboard() {
  const [rawAnalytics, setRawAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [dateRange, setDateRange] = useState<DateRange>("all");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [chartTrades, setChartTrades] = useState<Array<{timestamp:string;symbol:string;side:string;entry_price:number;exit_price:number;pnl:number;duration_minutes:number|null}>>([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const { toast } = useToast();

  useEffect(() => {
    document.title = `${TAB_LABELS[activeTab]} — TradeLoop Dashboard`;
  }, [activeTab]);

  useEffect(() => {
    api
      .get("/analytics/full")
      .then(({ data }) => setRawAnalytics(data))
      .catch((err: unknown) => {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          "Failed to load analytics";
        toast(msg, "error");
      })
      .finally(() => setLoading(false));
  }, [toast]);

  useEffect(() => {
    if (!selectedSymbol) { setChartTrades([]); return; }
    api.get(`/trades?per_page=200&symbol=${selectedSymbol}`)
      .then(({ data }) => setChartTrades(data.trades))
      .catch(() => setChartTrades([]));
  }, [selectedSymbol]);

  // Date-range-aware analytics: recompute overview from equity curve data
  const { analytics, filteredEquityCurve } = useMemo(() => {
    if (!rawAnalytics) return { analytics: null, filteredEquityCurve: [] };
    if (dateRange === "all") {
      return {
        analytics: rawAnalytics,
        filteredEquityCurve: rawAnalytics.equity_curve?.cumulative_pnl ?? [],
      };
    }

    const { from } = getDateRangeBounds(dateRange);
    if (!from) {
      return {
        analytics: rawAnalytics,
        filteredEquityCurve: rawAnalytics.equity_curve?.cumulative_pnl ?? [],
      };
    }

    const filteredCurve = (rawAnalytics.equity_curve?.cumulative_pnl ?? []).filter(
      (pt) => new Date(pt.date) >= from
    );

    return { analytics: rawAnalytics, filteredEquityCurve: filteredCurve };
  }, [rawAnalytics, dateRange]);

  const o = analytics?.overview;
  const isEmpty = !o || !o.total_trades;

  return (
    <div className="min-h-screen bg-bg-primary flex">
      {/* Sidebar — persistent app navigation */}
      <aside className="hidden md:flex flex-col w-56 bg-bg-card border-r border-border fixed h-screen z-40">
        <div className="p-4 border-b border-border">
          <Logo size="sm" />
        </div>

        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          <SidebarLink to="/dashboard" icon="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" label="Dashboard" active />
          <SidebarLink to="/insights" icon="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" label="Insights" accent />
          <SidebarLink to="/prop" icon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" label="Prop Firm" />
          <SidebarLink to="/report" icon="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" label="Weekly Report" />

          <div className="pt-3 pb-1 px-3"><span className="text-[10px] text-gray-600 uppercase tracking-wider font-semibold">Tools</span></div>
          <SidebarLink to="/upload" icon="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" label="Upload Trades" />
          <SidebarLink to="/connect" icon="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" label="Brokers" />

          <div className="pt-3 pb-1 px-3"><span className="text-[10px] text-gray-600 uppercase tracking-wider font-semibold">Account</span></div>
          <SidebarLink to="/settings" icon="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" label="Settings" />
        </nav>

        <div className="p-3 border-t border-border">
          <div className="flex items-center gap-2 px-2">
            <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center text-accent text-xs font-bold">
              {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "T"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-white truncate">{user?.name || user?.email}</p>
              <p className="text-[10px] text-gray-500 capitalize">{user?.plan} plan</p>
            </div>
            <button onClick={logout} className="text-gray-500 hover:text-white transition-colors" title="Log out">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content — offset by sidebar width */}
      <div className="flex-1 md:ml-56">
        <MarketTicker />

        {/* Mobile top bar */}
        <nav className="md:hidden sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
          <div className="px-4 flex items-center justify-between h-12">
            <Logo size="sm" />
            <div className="flex items-center gap-2">
              <Link to="/upload" className="btn-primary text-xs px-3 py-1">Upload</Link>
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-gray-400 hover:text-white p-1"
                aria-label="Toggle menu"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>
          {mobileMenuOpen && (
            <div className="bg-bg-card border-b border-border px-4 py-3 space-y-1">
              {[
                { to: "/dashboard", label: "Dashboard" },
                { to: "/insights", label: "Insights" },
                { to: "/prop", label: "Prop Firm" },
                { to: "/report", label: "Weekly Report" },
                { to: "/connect", label: "Brokers" },
                { to: "/settings", label: "Settings" },
              ].map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-bg-hover transition-colors"
                >
                  {item.label}
                </Link>
              ))}
              <button
                onClick={logout}
                className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-loss hover:bg-bg-hover transition-colors"
              >
                Log out
              </button>
            </div>
          )}
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {loading ? (
          <DashboardSkeleton />
        ) : isEmpty ? (
          <EmptyDashboard onSampleLoaded={() => {
            setLoading(true);
            api.get("/analytics/full").then(({ data }) => setRawAnalytics(data)).finally(() => setLoading(false));
          }} />
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
                      value={`+₹${o.average_winner?.toFixed(2)} ▲`}
                      positive={true}
                    />
                    <MetricCard
                      label="Avg Loser"
                      value={`-₹${o.average_loser?.toFixed(2)} ▼`}
                      positive={false}
                    />
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <MetricCard
                      label="Largest Winner"
                      value={`+₹${o.largest_winner?.toFixed(2)} ▲`}
                      positive={true}
                    />
                    <MetricCard
                      label="Largest Loser"
                      value={`-₹${Math.abs(o.largest_loser)?.toFixed(2)} ▼`}
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
                            ? `₹${analytics.risk_metrics.std_daily_pnl.toFixed(2)}`
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
                <div className="space-y-4">
                  <SymbolTable perSymbol={analytics.symbols.per_symbol} onSymbolClick={(sym) => setSelectedSymbol(sym === selectedSymbol ? null : sym)} selectedSymbol={selectedSymbol} />
                  {selectedSymbol && (
                    <LiveChart symbol={selectedSymbol} height={620} />
                  )}
                  {selectedSymbol && chartTrades.length > 0 && (
                    <TradeChart trades={chartTrades} symbol={selectedSymbol} />
                  )}
                </div>
              )}

              {activeTab === "trades" && <TradeTable />}
            </div>
          </>
        )}
      </main>
      </div>
    </div>
  );
}
