import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import Logo from "../components/Logo";
import { useAuth } from "../store/auth";

interface WeekComparison {
  pnl: number;
  pnl_change: number;
  win_rate: number;
  win_rate_change: number;
  trade_count: number;
  trade_count_change: number;
  revenge_trades: number;
  revenge_trade_change: number;
}

interface TopInsight {
  title: string;
  dollar_impact: number;
  recommendation: string;
}

interface GradeBreakdown {
  category: string;
  score: string;
  comment: string;
}

interface WeeklyReportData {
  week_start: string;
  week_end: string;
  grade: string;
  grade_reasoning: GradeBreakdown[];
  this_week: WeekComparison;
  last_week: WeekComparison | null;
  metrics: {
    trades: number;
    win_rate: number;
    pnl: number;
    avg_pnl: number;
  };
  top_insights: TopInsight[];
  focus_next_week: string;
  summary: string;
}

const GRADE_STYLES: Record<string, { color: string; bg: string }> = {
  A: { color: "text-emerald-400", bg: "bg-emerald-500/10" },
  B: { color: "text-teal-400", bg: "bg-teal-500/10" },
  C: { color: "text-yellow-400", bg: "bg-yellow-500/10" },
  D: { color: "text-orange-400", bg: "bg-orange-500/10" },
  F: { color: "text-red-400", bg: "bg-red-500/10" },
};

function gradeStyle(grade: string) {
  const letter = grade.charAt(0).toUpperCase();
  return GRADE_STYLES[letter] ?? GRADE_STYLES.C;
}

function formatDollar(value: number): string {
  const abs = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  if (value > 0) return `+$${abs}`;
  if (value < 0) return `-$${abs}`;
  return `$${abs}`;
}

function ChangeIndicator({ value, suffix = "", invert = false }: { value: number; suffix?: string; invert?: boolean }) {
  const isGood = invert ? value < 0 : value > 0;
  const isBad = invert ? value > 0 : value < 0;
  const arrow = value > 0 ? "\u25B2" : value < 0 ? "\u25BC" : "";
  const color = isGood ? "text-emerald-400" : isBad ? "text-red-400" : "text-gray-500";

  return (
    <span className={`text-xs font-mono ${color}`}>
      {arrow} {Math.abs(value).toFixed(suffix === "%" ? 1 : 2)}
      {suffix}
    </span>
  );
}

function ComparisonRow({
  label,
  current,
  change,
  format = "dollar",
  invert = false,
}: {
  label: string;
  current: number;
  change: number;
  format?: "dollar" | "percent" | "number";
  invert?: boolean;
}) {
  let display: string;
  let changeSuffix = "";
  if (format === "dollar") {
    display = formatDollar(current);
    changeSuffix = "";
  } else if (format === "percent") {
    display = `${current.toFixed(1)}%`;
    changeSuffix = "%";
  } else {
    display = `${current}`;
    changeSuffix = "";
  }

  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <div className="flex items-center gap-3">
        <span className="text-sm font-mono text-white">{display}</span>
        <ChangeIndicator value={change} suffix={changeSuffix} invert={invert} />
      </div>
    </div>
  );
}

function ReportSkeleton() {
  return (
    <div className="animate-pulse space-y-6 max-w-2xl mx-auto">
      <div className="flex justify-center">
        <div className="w-24 h-24 bg-bg-card rounded-full" />
      </div>
      <div className="h-6 bg-bg-card rounded w-48 mx-auto" />
      <div className="h-40 bg-bg-card rounded-xl" />
      <div className="h-32 bg-bg-card rounded-xl" />
      <div className="h-48 bg-bg-card rounded-xl" />
    </div>
  );
}

export default function WeeklyReport() {
  const [report, setReport] = useState<WeeklyReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [shared, setShared] = useState(false);
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  useEffect(() => {
    document.title = "Weekly Report — TradeLoop";
  }, []);

  useEffect(() => {
    api
      .get("/reports/weekly")
      .then(({ data }) => setReport(data))
      .catch((err: unknown) => {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          "Failed to load report";
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, []);

  function handleShare() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      setShared(true);
      setTimeout(() => setShared(false), 2000);
    });
  }

  const gs = report ? gradeStyle(report.grade) : null;

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border print:hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 hidden sm:block">{user?.email}</span>
            <Link to="/dashboard" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
              Dashboard
            </Link>
            <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8" aria-label="Weekly performance report">
        {loading ? (
          <ReportSkeleton />
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-400 mb-4">{error}</p>
            <Link to="/dashboard" className="btn-primary">
              Back to Dashboard
            </Link>
          </div>
        ) : !report ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-20">&#x1f4c5;</div>
            <h2 className="text-2xl font-bold text-white mb-2">No trades this week</h2>
            <p className="text-gray-400 mb-6">Upload your trades to generate a weekly report card.</p>
            <Link to="/upload" className="btn-primary">
              Upload Trades
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            <header className="text-center">
              <p className="text-xs text-gray-500 mb-4 uppercase tracking-wider">
                {report.week_start} &mdash; {report.week_end}
              </p>

              <div
                className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${gs!.bg} mb-4`}
                aria-label={`Grade: ${report.grade}`}
              >
                <span className={`text-5xl font-bold font-mono ${gs!.color}`}>
                  {report.grade}
                </span>
              </div>

              <h1 className="text-xl font-bold text-white">Weekly Report Card</h1>
            </header>

            {report.grade_reasoning.length > 0 && (
              <section className="bg-bg-card rounded-xl border border-border p-5" aria-label="Grade breakdown">
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  Grade Breakdown
                </h2>
                <div className="space-y-2">
                  {report.grade_reasoning.map((r, i) => (
                    <div key={i} className="flex items-start justify-between gap-3 text-sm">
                      <div className="flex-1">
                        <span className="text-gray-300">{r.category}</span>
                        <span className="text-gray-500 ml-2 text-xs">{r.comment}</span>
                      </div>
                      <span className="text-white font-mono text-xs font-bold">{r.score}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {report.last_week && (
              <section className="bg-bg-card rounded-xl border border-border p-5" aria-label="Week over week comparison">
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  This Week vs Last Week
                </h2>
                <ComparisonRow
                  label="P&L"
                  current={report.this_week.pnl}
                  change={report.this_week.pnl_change}
                  format="dollar"
                />
                <ComparisonRow
                  label="Win Rate"
                  current={report.this_week.win_rate}
                  change={report.this_week.win_rate_change}
                  format="percent"
                />
                <ComparisonRow
                  label="Trades"
                  current={report.this_week.trade_count}
                  change={report.this_week.trade_count_change}
                  format="number"
                />
                <ComparisonRow
                  label="Revenge Trades"
                  current={report.this_week.revenge_trades}
                  change={report.this_week.revenge_trade_change}
                  format="number"
                  invert
                />
              </section>
            )}

            <section className="bg-bg-card rounded-xl border border-border p-5" aria-label="Key metrics">
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                Key Metrics
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold font-mono text-white">{report.metrics.trades}</p>
                  <p className="text-xs text-gray-500 mt-1">Trades</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold font-mono text-white">
                    {report.metrics.win_rate.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Win Rate</p>
                </div>
                <div className="text-center">
                  <p
                    className={`text-2xl font-bold font-mono ${
                      report.metrics.pnl >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {formatDollar(report.metrics.pnl)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">P&amp;L</p>
                </div>
                <div className="text-center">
                  <p
                    className={`text-2xl font-bold font-mono ${
                      report.metrics.avg_pnl >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {formatDollar(report.metrics.avg_pnl)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Avg P&amp;L</p>
                </div>
              </div>
            </section>

            {report.top_insights.length > 0 && (
              <section className="bg-bg-card rounded-xl border border-border p-5" aria-label="Top insights">
                <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                  Top Insights
                </h2>
                <div className="space-y-4">
                  {report.top_insights.map((insight, i) => (
                    <div key={i} className="border-b border-border pb-4 last:border-0 last:pb-0">
                      <div className="flex items-start justify-between gap-3 mb-1">
                        <h3 className="text-sm font-medium text-gray-300">{insight.title}</h3>
                        <span
                          className={`text-sm font-bold font-mono whitespace-nowrap ${
                            insight.dollar_impact >= 0 ? "text-emerald-400" : "text-red-400"
                          }`}
                        >
                          {formatDollar(insight.dollar_impact)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">{insight.recommendation}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {report.focus_next_week && (
              <section
                className="bg-gradient-to-r from-accent/5 to-accent/10 rounded-xl border border-accent/20 p-5"
                aria-label="Focus for next week"
              >
                <h2 className="text-xs font-semibold text-accent uppercase tracking-wider mb-2">
                  Focus for Next Week
                </h2>
                <p className="text-sm text-gray-300 leading-relaxed">{report.focus_next_week}</p>
              </section>
            )}

            {report.summary && (
              <section className="bg-bg-card rounded-xl border border-border p-5" aria-label="Summary">
                <p className="text-sm text-gray-400 leading-relaxed">{report.summary}</p>
              </section>
            )}

            <div className="flex justify-center pt-2 print:hidden">
              <button
                onClick={handleShare}
                className="btn-primary text-sm px-6 py-2.5 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                  />
                </svg>
                {shared ? "Link Copied!" : "Share Report"}
              </button>
            </div>

            <footer className="text-center pt-4 pb-8">
              <Logo size="sm" showText={false} />
              <p className="text-[10px] text-gray-600 mt-2">Generated by TradeLoop</p>
            </footer>
          </div>
        )}
      </main>
    </div>
  );
}
