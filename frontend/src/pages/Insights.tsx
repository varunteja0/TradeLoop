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
  type: string;
  severity: "critical" | "major" | "minor" | "positive";
  title: string;
  description: string;
  dollar_impact: number;
  monthly_projection: number;
  recommendation: string;
  affected_trades: number;
  equity_curve?: EquityPoint[];
}

interface InsightsResponse {
  actual_total_pnl: number;
  potential_total_pnl: number;
  insights: Insight[];
}

const SEVERITY_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  critical: { bg: "bg-red-500/20", text: "text-red-400", label: "Critical" },
  major: { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "Major" },
  minor: { bg: "bg-gray-500/20", text: "text-gray-400", label: "Minor" },
  positive: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "Edge" },
};

function formatDollar(value: number): string {
  const abs = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  if (value > 0) return `+$${abs}`;
  if (value < 0) return `-$${abs}`;
  return `$${abs}`;
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
            {insight.affected_trades} trade{insight.affected_trades !== 1 ? "s" : ""} affected
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
                      tickFormatter={(v: number) => `$${v}`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#12121a",
                        border: "1px solid #1e1e2e",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(value: number, name: string) => [
                        `$${value.toFixed(2)}`,
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

export default function Insights() {
  const [data, setData] = useState<InsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  useEffect(() => {
    document.title = "Insights — TradeLoop";
  }, []);

  useEffect(() => {
    api
      .get("/insights/full")
      .then(({ data }) => setData(data))
      .catch((err: unknown) => {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          "Failed to load insights";
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, []);

  const sortedInsights = (data?.insights ?? [])
    .slice()
    .sort((a, b) => Math.abs(b.dollar_impact) - Math.abs(a.dollar_impact));

  const costInsights = sortedInsights.filter((i) => i.dollar_impact <= 0);
  const edgeInsights = sortedInsights.filter((i) => i.dollar_impact > 0);

  const gap = (data?.potential_total_pnl ?? 0) - (data?.actual_total_pnl ?? 0);

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
        {loading ? (
          <InsightsSkeleton />
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-400 mb-4">{error}</p>
            <Link to="/dashboard" className="btn-primary">
              Back to Dashboard
            </Link>
          </div>
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
                  ${Math.abs(gap).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </span>{" "}
                on the table. Here&rsquo;s exactly where.
              </h1>
              <div className="flex flex-wrap gap-6 text-sm">
                <div>
                  <p className="text-gray-500 text-xs">Actual P&amp;L</p>
                  <p className={`font-mono font-bold ${data.actual_total_pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {formatDollar(data.actual_total_pnl)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Potential P&amp;L</p>
                  <p className="text-accent font-mono font-bold">
                    {formatDollar(data.potential_total_pnl)}
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
