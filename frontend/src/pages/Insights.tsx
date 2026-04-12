import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import api from "../api/client";
import Logo from "../components/Logo";
import { useAuth } from "../store/auth";

interface EquityPoint {
  date: string;
  actual: number;
  counterfactual: number;
}

interface Insight {
  id: string;
  category: string;
  severity: "critical" | "major" | "minor" | "positive";
  title: string;
  description: string;
  dollar_impact: number;
  monthly_projection: number;
  recommendation: string;
  affected_trade_count: number;
  equity_curve?: EquityPoint[];
  confidence: number;
  stats: Record<string, unknown>;
}

interface InsightsResponse {
  summary: {
    actual_total_pnl: number;
    potential_total_pnl: number;
    total_leaks_found: number;
    total_money_leaked: number;
    projected_monthly_savings: number;
  };
  insights: Insight[];
}

const SEVERITY_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  critical: { bg: "bg-red-500/20", text: "text-red-400", label: "Critical" },
  major: { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "Major" },
  minor: { bg: "bg-gray-500/20", text: "text-gray-400", label: "Minor" },
  positive: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "Edge" },
};

function formatDollar(value: number): string {
  const abs = Math.abs(value).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  if (value > 0) return `+₹${abs}`;
  if (value < 0) return `-₹${abs}`;
  return `₹${abs}`;
}

function SkeletonCard() {
  return (
    <div className="bg-bg-card rounded-xl p-6 animate-pulse border border-border">
      <div className="flex items-center gap-2 mb-4">
        <div className="h-5 w-16 bg-bg-hover rounded-full" />
        <div className="h-5 w-40 bg-bg-hover rounded" />
      </div>
      <div className="h-10 w-32 bg-bg-hover rounded mb-2" />
      <div className="h-4 w-24 bg-bg-hover rounded mb-4" />
      <div className="h-4 bg-bg-hover rounded w-full mb-2" />
      <div className="h-4 bg-bg-hover rounded w-3/4" />
    </div>
  );
}

function InsightsSkeleton() {
  return (
    <>
      <div className="bg-bg-card rounded-xl p-8 animate-pulse border border-border mb-8">
        <div className="h-6 w-96 bg-bg-hover rounded mb-3" />
        <div className="h-10 w-64 bg-bg-hover rounded" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </>
  );
}

function InsightCard({
  insight,
  expanded,
  onToggle,
}: {
  insight: Insight;
  expanded: boolean;
  onToggle: () => void;
}) {
  const sev = SEVERITY_STYLES[insight.severity] ?? SEVERITY_STYLES.minor;
  const isPositive = insight.dollar_impact > 0;
  const isCritical = insight.severity === "critical";

  return (
    <article
      className="bg-bg-card rounded-xl border border-border hover:border-border/80 transition-colors"
      {...(isCritical ? { role: "alert" } : {})}
    >
      <button
        onClick={onToggle}
        className="w-full text-left p-6 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-xl"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2 mb-3">
          <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${sev.bg} ${sev.text}`}>
            {sev.label}
          </span>
          <h3 className="text-sm font-medium text-gray-300">{insight.title}</h3>
        </div>

        <p
          className={`text-3xl font-bold font-mono mb-1 ${
            isPositive ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {formatDollar(insight.dollar_impact)}
        </p>
        <p className="text-xs text-gray-500 mb-3">
          ~{formatDollar(insight.monthly_projection)}/month
        </p>

        <p className="text-sm text-gray-400 leading-relaxed">{insight.description}</p>

        <div className="flex items-center gap-1 mt-3 text-xs text-gray-500">
          <svg
            className={`w-3 h-3 transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
          <span>{expanded ? "Hide details" : "Show details"}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-6 pb-6 border-t border-border pt-4 space-y-4">
          <div className="bg-bg-primary rounded-lg p-4">
            <p className="text-xs font-semibold text-accent mb-1 uppercase tracking-wider">
              Recommendation
            </p>
            <p className="text-sm text-gray-300 leading-relaxed">{insight.recommendation}</p>
          </div>

          <p className="text-xs text-gray-500">
            {insight.affected_trade_count} trade{insight.affected_trade_count !== 1 ? "s" : ""} affected
          </p>

          {insight.equity_curve && insight.equity_curve.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                What-If Equity Curve
              </p>
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={insight.equity_curve}>
                    <defs>
                      <linearGradient id={`actual-${insight.id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6b7280" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#6b7280" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id={`cf-${insight.id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 10, fill: "#6b7280" }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 10, fill: "#6b7280" }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v: number) => `₹${v}`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#12121a",
                        border: "1px solid #1e1e2e",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(value: number, name: string) => [
                        `₹${value.toFixed(2)}`,
                        name === "actual" ? "Actual" : "Without This Pattern",
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="actual"
                      stroke="#6b7280"
                      fill={`url(#actual-${insight.id})`}
                      strokeWidth={1.5}
                      dot={false}
                    />
                    <Area
                      type="monotone"
                      dataKey="counterfactual"
                      stroke="#00d4aa"
                      fill={`url(#cf-${insight.id})`}
                      strokeWidth={2}
                      dot={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-0.5 bg-gray-500 inline-block rounded" />
                  Actual
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-0.5 bg-accent inline-block rounded" />
                  Without This Pattern
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

interface Alert {
  id: string;
  type: string;
  severity: "critical" | "warning" | "insight";
  title: string;
  message: string;
  dollar_impact: number | null;
  affected_trades: number;
  recommendation: string | null;
}

interface AlertsResponse {
  alerts: Alert[];
  total_alerts: number;
  summary: {
    total_trades: number;
    total_pnl: number;
    mood_tagged_pct: number;
    rule_followed_pct: number | null;
  } | null;
}

const ALERT_SEVERITY_STYLES: Record<string, { bg: string; border: string; icon: string }> = {
  critical: { bg: "bg-red-500/10", border: "border-red-500/30", icon: "text-red-400" },
  warning: { bg: "bg-yellow-500/10", border: "border-yellow-500/30", icon: "text-yellow-400" },
  insight: { bg: "bg-blue-500/10", border: "border-blue-500/30", icon: "text-blue-400" },
};

export default function Insights() {
  const [data, setData] = useState<InsightsResponse | null>(null);
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<"counterfactual" | "alerts">("alerts");
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  useEffect(() => {
    document.title = "Insights — TradeLoop";
  }, []);

  useEffect(() => {
    const extractMsg = (err: unknown) =>
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
      "Failed to load";

    Promise.all([
      api.get("/insights/full").then(({ data }) => setData(data)).catch((err) => {
        setError((prev) => prev || extractMsg(err));
      }),
      api.get("/insights/alerts").then(({ data }) => setAlerts(data)).catch((err) => {
        setError((prev) => prev || extractMsg(err));
      }),
    ]).finally(() => setLoading(false));
  }, []);

  const sortedInsights = (data?.insights ?? [])
    .slice()
    .sort((a, b) => Math.abs(b.dollar_impact) - Math.abs(a.dollar_impact));

  const costInsights = sortedInsights.filter((i) => i.dollar_impact <= 0);
  const edgeInsights = sortedInsights.filter((i) => i.dollar_impact > 0);

  const gap = (data?.summary?.potential_total_pnl ?? 0) - (data?.summary?.actual_total_pnl ?? 0);

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 hidden sm:block">{user?.email}</span>
            <Link to="/dashboard" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
              Dashboard
            </Link>
            <Link to="/upload" className="btn-primary text-xs px-3 py-1.5">
              Upload Trades
            </Link>
            <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveView("alerts")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeView === "alerts"
                ? "bg-accent text-bg-primary"
                : "text-gray-400 hover:text-white hover:bg-bg-hover"
            }`}
          >
            Intelligence Alerts
            {alerts && alerts.total_alerts > 0 && (
              <span className="ml-2 bg-red-500/20 text-red-400 text-xs px-1.5 py-0.5 rounded-full">
                {alerts.total_alerts}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveView("counterfactual")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeView === "counterfactual"
                ? "bg-accent text-bg-primary"
                : "text-gray-400 hover:text-white hover:bg-bg-hover"
            }`}
          >
            Counterfactual Analysis
          </button>
        </div>

        {loading ? (
          <InsightsSkeleton />
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-400 mb-4">{error}</p>
            <Link to="/dashboard" className="btn-primary">
              Back to Dashboard
            </Link>
          </div>
        ) : activeView === "alerts" ? (
          alerts && alerts.alerts.length > 0 ? (
            <div className="space-y-4">
              {alerts.summary && (
                <div className="bg-gradient-to-r from-bg-card to-bg-hover rounded-xl p-6 border border-border mb-6">
                  <h2 className="text-lg font-bold text-white mb-1">Behavioral Intelligence</h2>
                  <p className="text-sm text-gray-400">
                    {alerts.total_alerts} pattern{alerts.total_alerts !== 1 ? "s" : ""} detected across {alerts.summary.total_trades} trades.
                    {alerts.summary.mood_tagged_pct > 0 && (
                      <span> {Math.round(alerts.summary.mood_tagged_pct)}% mood-tagged.</span>
                    )}
                  </p>
                </div>
              )}
              {alerts.alerts.map((alert, idx) => {
                const sev = ALERT_SEVERITY_STYLES[alert.severity] ?? ALERT_SEVERITY_STYLES.insight;
                return (
                  <div key={idx} className={`rounded-xl p-5 border ${sev.bg} ${sev.border}`}>
                    <div className="flex items-start gap-3">
                      <span className={`text-lg ${sev.icon} mt-0.5`}>
                        {alert.severity === "critical" ? "🚨" : alert.severity === "warning" ? "⚠️" : "💡"}
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-sm font-semibold text-white">{alert.title}</h3>
                          {alert.dollar_impact != null && alert.dollar_impact !== 0 && (
                            <span className={`text-xs font-mono font-bold ${alert.dollar_impact < 0 ? "text-red-400" : "text-emerald-400"}`}>
                              {formatDollar(alert.dollar_impact)}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed">{alert.message}</p>
                        {alert.recommendation && (
                          <p className="text-xs text-accent mt-2">{alert.recommendation}</p>
                        )}
                        {alert.affected_trades > 0 && (
                          <p className="text-xs text-gray-500 mt-1">
                            {alert.affected_trades} trade{alert.affected_trades !== 1 ? "s" : ""} affected
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-20">
              <div className="text-6xl mb-4 opacity-20">&#x1f50d;</div>
              <h2 className="text-2xl font-bold text-white mb-2">No alerts yet</h2>
              <p className="text-gray-400 mb-6">
                Upload trades and tag your moods to unlock behavioral intelligence.
              </p>
              <Link to="/upload" className="btn-primary">
                Upload Trades
              </Link>
            </div>
          )
        ) : !data || data.insights.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-20">&#x1f50d;</div>
            <h2 className="text-2xl font-bold text-white mb-2">No insights yet</h2>
            <p className="text-gray-400 mb-6">
              Upload more trades to unlock counterfactual analysis.
            </p>
            <Link to="/upload" className="btn-primary">
              Upload Trades
            </Link>
          </div>
        ) : (
          <>
            <div className="bg-gradient-to-r from-bg-card to-bg-hover rounded-xl p-8 border border-border mb-8">
              <p className="text-gray-400 text-sm mb-2">Counterfactual Analysis</p>
              <h1 className="text-xl sm:text-2xl font-bold text-white mb-3">
                You left{" "}
                <span className="text-red-400 font-mono">
                  ₹{Math.abs(gap).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>{" "}
                on the table. Here&rsquo;s exactly where.
              </h1>
              <div className="flex flex-wrap gap-6 text-sm">
                <div>
                  <p className="text-gray-500 text-xs">Actual P&amp;L</p>
                  <p className={`font-mono font-bold ${(data.summary?.actual_total_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {formatDollar(data.summary?.actual_total_pnl ?? 0)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Potential P&amp;L</p>
                  <p className="text-accent font-mono font-bold">
                    {formatDollar(data.summary?.potential_total_pnl ?? 0)}
                  </p>
                </div>
              </div>
            </div>

            {costInsights.length > 0 && (
              <section aria-label="Costly patterns">
                <h2 className="text-lg font-semibold text-white mb-4">
                  Patterns Costing You Money
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
                  {costInsights.map((insight) => (
                    <InsightCard
                      key={insight.id}
                      insight={insight}
                      expanded={expandedId === insight.id}
                      onToggle={() =>
                        setExpandedId((prev) => (prev === insight.id ? null : insight.id))
                      }
                    />
                  ))}
                </div>
              </section>
            )}

            {edgeInsights.length > 0 && (
              <section aria-label="Positive edges">
                <h2 className="text-lg font-semibold text-white mb-4">Your Edges</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {edgeInsights.map((insight) => (
                    <InsightCard
                      key={insight.id}
                      insight={insight}
                      expanded={expandedId === insight.id}
                      onToggle={() =>
                        setExpandedId((prev) => (prev === insight.id ? null : insight.id))
                      }
                    />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
