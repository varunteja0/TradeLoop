import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import Logo from "../components/Logo";
import { useAuth } from "../store/auth";
import { useToast } from "../components/Toast";

interface WeekMetrics {
  total_trades: number;
  winners: number;
  losers: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
  largest_winner: number;
  largest_loser: number;
  revenge_trades: number;
  trading_days: number;
  avg_trades_per_day: number;
}

interface Comparison {
  pnl_change: number;
  win_rate_change: number;
  trade_count_change: number;
  revenge_change: number;
  improved: boolean;
}

interface FocusArea {
  area: string;
  why: string;
  action: string;
  potential_savings: number | null;
}

interface InsightSummary {
  id: string;
  title: string;
  dollar_impact: number;
  recommendation: string;
  severity: string;
}

interface WeeklyReportData {
  has_data: boolean;
  message?: string;
  period?: { start: string; end: string };
  this_week?: WeekMetrics;
  previous_week?: WeekMetrics | null;
  comparison?: Comparison | null;
  grade?: string;
  grade_reasons?: string[];
  top_insights?: InsightSummary[];
  focus_for_next_week?: FocusArea;
  summary?: string;
}

const GRADE_COLORS: Record<string, string> = {
  A: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10",
  B: "text-teal-400 border-teal-400/30 bg-teal-400/10",
  C: "text-yellow-400 border-yellow-400/30 bg-yellow-400/10",
  D: "text-orange-400 border-orange-400/30 bg-orange-400/10",
  F: "text-red-400 border-red-400/30 bg-red-400/10",
};

function formatDollar(v: number): string {
  const abs = Math.abs(v).toFixed(2);
  if (v > 0) return `+₹${abs}`;
  if (v < 0) return `-₹${abs}`;
  return `₹${abs}`;
}

function ChangeIndicator({ value, suffix = "" }: { value: number; suffix?: string }) {
  if (value === 0) return <span className="text-gray-500">—</span>;
  return (
    <span className={value > 0 ? "text-win" : "text-loss"}>
      {value > 0 ? "▲" : "▼"} {Math.abs(value).toFixed(suffix === "%" ? 1 : 2)}{suffix}
    </span>
  );
}

export default function WeeklyReport() {
  const [report, setReport] = useState<WeeklyReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [weekOf, setWeekOf] = useState("");
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const { toast } = useToast();

  useEffect(() => {
    document.title = "Weekly Report — TradeLoop";
  }, []);

  const fetchReport = (dateParam?: string) => {
    setLoading(true);
    const url = dateParam ? `/reports/weekly?week_of=${dateParam}` : "/reports/weekly";
    api.get(url)
      .then(({ data }) => setReport(data))
      .catch(() => toast("Failed to load report", "error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchReport(); }, []);

  const handleDateChange = () => {
    if (weekOf) fetchReport(weekOf);
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    toast("Report URL copied to clipboard", "success");
  };

  const gradeStyle = GRADE_COLORS[report?.grade ?? "C"] ?? GRADE_COLORS.C;
  const tw = report?.this_week;
  const comp = report?.comparison;

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border print:hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />
          <div className="flex items-center gap-3">
            <Link to="/dashboard" className="text-xs text-gray-400 hover:text-white transition-colors">Dashboard</Link>
            <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">Log out</button>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {/* Date picker for historical reports */}
        <div className="flex items-center gap-3 mb-6 print:hidden">
          <label htmlFor="week-of" className="text-sm text-gray-400">Report for week of:</label>
          <input id="week-of" type="date" value={weekOf} onChange={(e) => setWeekOf(e.target.value)}
            className="input-field !w-auto text-sm !px-3 !py-1.5" />
          <button onClick={handleDateChange} disabled={!weekOf} className="btn-primary text-xs px-3 py-1.5 disabled:opacity-30">
            Load
          </button>
        </div>

        {loading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-32 bg-bg-card rounded-xl" />
            <div className="grid grid-cols-2 gap-4">
              <div className="h-24 bg-bg-card rounded-xl" />
              <div className="h-24 bg-bg-card rounded-xl" />
            </div>
          </div>
        ) : !report?.has_data ? (
          <div className="text-center py-20">
            <div className="text-5xl mb-4 opacity-30">&#x1f4ca;</div>
            <h2 className="text-2xl font-bold text-white mb-2">No Trades This Week</h2>
            <p className="text-gray-400 mb-2">{report?.message || "Upload trades or try a different date range."}</p>
            <p className="text-gray-500 text-sm mb-6">Tip: Use the date picker above to view historical reports.</p>
            <Link to="/upload" className="btn-primary">Upload Trades</Link>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Grade */}
            <div className="text-center">
              {report.period && (
                <p className="text-xs text-gray-500 mb-4">
                  {report.period.start} — {report.period.end}
                </p>
              )}
              <div className={`inline-flex items-center justify-center w-28 h-28 rounded-full border-4 ${gradeStyle}`}>
                <span className="text-6xl font-black">{report.grade}</span>
              </div>
              <p className="text-sm text-gray-400 mt-3">Weekly Trading Grade</p>
            </div>

            {/* Grade reasons */}
            {report.grade_reasons && report.grade_reasons.length > 0 && (
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Grade Breakdown</h3>
                <div className="space-y-1.5">
                  {report.grade_reasons.map((reason, i) => {
                    const isPositive = reason.startsWith("+");
                    return (
                      <p key={i} className={`text-sm font-mono ${isPositive ? "text-win" : "text-loss"}`}>
                        {reason}
                      </p>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Key metrics */}
            {tw && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="card text-center">
                  <p className="text-xs text-gray-500 mb-1">Trades</p>
                  <p className="text-2xl font-bold text-white font-mono">{tw.total_trades}</p>
                  {comp && <ChangeIndicator value={comp.trade_count_change} />}
                </div>
                <div className="card text-center">
                  <p className="text-xs text-gray-500 mb-1">Win Rate</p>
                  <p className="text-2xl font-bold text-white font-mono">{tw.win_rate}%</p>
                  {comp && <ChangeIndicator value={comp.win_rate_change} suffix="%" />}
                </div>
                <div className="card text-center">
                  <p className="text-xs text-gray-500 mb-1">P&L</p>
                  <p className={`text-2xl font-bold font-mono ${tw.total_pnl >= 0 ? "text-win" : "text-loss"}`}>
                    {formatDollar(tw.total_pnl)}
                  </p>
                  {comp && <ChangeIndicator value={comp.pnl_change} />}
                </div>
                <div className="card text-center">
                  <p className="text-xs text-gray-500 mb-1">Avg P&L</p>
                  <p className={`text-2xl font-bold font-mono ${tw.avg_pnl >= 0 ? "text-win" : "text-loss"}`}>
                    {formatDollar(tw.avg_pnl)}
                  </p>
                </div>
              </div>
            )}

            {/* Week-over-week comparison */}
            {comp && report.previous_week && (
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">vs Last Week</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">P&L Change</p>
                    <p className={`font-mono font-bold ${comp.pnl_change >= 0 ? "text-win" : "text-loss"}`}>
                      {formatDollar(comp.pnl_change)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Win Rate Change</p>
                    <ChangeIndicator value={comp.win_rate_change} suffix="%" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Trade Count</p>
                    <ChangeIndicator value={comp.trade_count_change} />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Revenge Trades</p>
                    <ChangeIndicator value={-comp.revenge_change} />
                  </div>
                </div>
              </div>
            )}

            {/* Top insights */}
            {report.top_insights && report.top_insights.length > 0 && (
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Top Insights</h3>
                <div className="space-y-3">
                  {report.top_insights.map((insight, i) => (
                    <div key={i} className="flex items-start gap-3 py-2 border-b border-border last:border-0">
                      <span className={`text-lg font-bold font-mono shrink-0 ${
                        insight.dollar_impact < 0 ? "text-loss" : "text-win"}`}>
                        {formatDollar(insight.dollar_impact)}
                      </span>
                      <div>
                        <p className="text-sm text-white font-medium">{insight.title}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{insight.recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Focus for next week */}
            {report.focus_for_next_week && (
              <div className="card border-accent/20">
                <h3 className="text-sm font-semibold text-accent mb-2">Focus for Next Week</h3>
                <p className="text-white font-medium mb-1">{report.focus_for_next_week.area}</p>
                <p className="text-sm text-gray-400 mb-2">{report.focus_for_next_week.why}</p>
                <p className="text-sm text-gray-300 bg-bg-primary rounded-lg p-3">
                  {report.focus_for_next_week.action}
                </p>
                {report.focus_for_next_week.potential_savings != null && (
                  <p className="text-xs text-accent mt-2">
                    Potential savings: {formatDollar(report.focus_for_next_week.potential_savings)}/month
                  </p>
                )}
              </div>
            )}

            {/* Summary */}
            {report.summary && (
              <p className="text-center text-sm text-gray-500 italic">{report.summary}</p>
            )}

            {/* Share */}
            <div className="text-center print:hidden">
              <button onClick={handleShare} className="btn-secondary text-sm">
                Share Report
              </button>
            </div>

            {/* Footer branding */}
            <p className="text-center text-xs text-gray-600 mt-8">
              Generated by TradeLoop &middot; tradeloop.io
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
