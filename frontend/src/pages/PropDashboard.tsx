import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import Logo from "../components/Logo";
import { useAuth } from "../store/auth";

interface PropAccount {
  id: string;
  firm: string;
  balance: number;
  phase: string;
  created_at: string;
}

interface RuleStatus {
  name: string;
  type: "daily_loss" | "max_drawdown" | "profit_target" | "trading_days" | "consistency";
  current: number;
  limit: number;
  remaining: number;
  unit: "currency" | "percent" | "days";
  passed: boolean;
  trailing?: boolean;
  peak?: number;
  details?: string;
}

interface Warning {
  level: "warning" | "critical";
  message: string;
  timestamp: string;
  rule: string;
}

interface ComplianceData {
  status: "safe" | "warning" | "critical" | "violated";
  risk_score: number;
  rules: RuleStatus[];
  warnings: Warning[];
  violations: string[];
}

const FIRM_PRESETS = ["FTMO", "FundingPips", "MyForexFunds", "The5ers", "TopStep", "Other"];
const PHASE_OPTIONS = ["Evaluation", "Verification", "Funded"];

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string; border: string }> = {
  safe: { bg: "bg-emerald-500/10", text: "text-emerald-400", label: "SAFE", border: "border-emerald-500/30" },
  warning: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "WARNING", border: "border-yellow-500/30" },
  critical: { bg: "bg-red-500/10", text: "text-red-400", label: "CRITICAL", border: "border-red-500/30" },
  violated: { bg: "bg-red-900/20", text: "text-red-500", label: "VIOLATED", border: "border-red-600/50" },
};

function formatValue(value: number, unit: string): string {
  if (unit === "currency") return `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (unit === "percent") return `${value.toFixed(1)}%`;
  return `${value}`;
}

function ruleProgress(rule: RuleStatus): number {
  if (rule.limit === 0) return 0;
  return Math.min((rule.current / rule.limit) * 100, 100);
}

function ruleColor(rule: RuleStatus): string {
  if (!rule.passed) return "bg-red-500";
  const pct = ruleProgress(rule);
  if (rule.type === "profit_target" || rule.type === "trading_days") {
    if (pct >= 100) return "bg-emerald-400";
    if (pct >= 60) return "bg-accent";
    return "bg-gray-500";
  }
  if (pct >= 90) return "bg-red-500";
  if (pct >= 70) return "bg-yellow-500";
  return "bg-accent";
}

function RiskGauge({ score }: { score: number }) {
  const radius = 60;
  const circumference = Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color =
    score <= 30 ? "#00d4aa" : score <= 60 ? "#eab308" : score <= 80 ? "#f97316" : "#ff4757";

  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="80" viewBox="0 0 140 80" role="img" aria-label={`Risk score: ${score}`}>
        <path
          d="M 10 75 A 60 60 0 0 1 130 75"
          fill="none"
          stroke="#1e1e2e"
          strokeWidth="10"
          strokeLinecap="round"
        />
        <path
          d="M 10 75 A 60 60 0 0 1 130 75"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <p className="text-3xl font-bold font-mono text-white -mt-4">{score}</p>
      <p className="text-xs text-gray-500 mt-1">Risk Score</p>
    </div>
  );
}

function RuleCard({ rule }: { rule: RuleStatus }) {
  const pct = ruleProgress(rule);
  const barColor = ruleColor(rule);
  const isGoal = rule.type === "profit_target" || rule.type === "trading_days";
  const label = rule.name;

  return (
    <div className="bg-bg-card rounded-xl border border-border p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-300">{label}</h3>
        {!rule.passed && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">
            FAILED
          </span>
        )}
        {rule.trailing && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-500">
            Trailing
          </span>
        )}
      </div>

      <div
        className="w-full h-2 bg-bg-hover rounded-full overflow-hidden mb-2"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${pct.toFixed(0)}%`}
      >
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="flex justify-between text-xs">
        <span className="text-gray-400">
          {formatValue(rule.current, rule.unit)} / {formatValue(rule.limit, rule.unit)}
        </span>
        <span className={isGoal ? "text-accent" : "text-gray-500"}>
          {isGoal
            ? `${(100 - pct).toFixed(0)}% remaining`
            : `${formatValue(rule.remaining, rule.unit)} left`}
        </span>
      </div>

      {rule.peak != null && (
        <p className="text-[10px] text-gray-500 mt-1">Peak: {formatValue(rule.peak, rule.unit)}</p>
      )}
      {rule.details && (
        <p className="text-[10px] text-gray-500 mt-1">{rule.details}</p>
      )}
    </div>
  );
}

export default function PropDashboard() {
  const [accounts, setAccounts] = useState<PropAccount[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [compliance, setCompliance] = useState<ComplianceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [complianceLoading, setComplianceLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formFirm, setFormFirm] = useState(FIRM_PRESETS[0]);
  const [formBalance, setFormBalance] = useState("");
  const [formPhase, setFormPhase] = useState(PHASE_OPTIONS[0]);
  const [submitting, setSubmitting] = useState(false);
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  useEffect(() => {
    document.title = "Prop Compliance — TradeLoop";
  }, []);

  useEffect(() => {
    api
      .get("/prop")
      .then(({ data }) => {
        setAccounts(data);
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const loadCompliance = useCallback((id: string) => {
    setComplianceLoading(true);
    api
      .get(`/prop/${id}/compliance`)
      .then(({ data }) => setCompliance(data))
      .catch(() => setCompliance(null))
      .finally(() => setComplianceLoading(false));
  }, []);

  useEffect(() => {
    if (selectedId) loadCompliance(selectedId);
  }, [selectedId, loadCompliance]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formBalance || submitting) return;
    setSubmitting(true);
    try {
      const { data } = await api.post("/prop", {
        firm: formFirm,
        balance: parseFloat(formBalance),
        phase: formPhase,
      });
      setAccounts((prev) => [...prev, data]);
      setSelectedId(data.id);
      setShowForm(false);
      setFormBalance("");
    } catch {
      /* handled by interceptor */
    } finally {
      setSubmitting(false);
    }
  }

  const selectedAccount = accounts.find((a) => a.id === selectedId);
  const status = compliance ? STATUS_STYLES[compliance.status] ?? STATUS_STYLES.safe : null;

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
            <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {loading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-10 w-64 bg-bg-card rounded" />
            <div className="h-40 bg-bg-card rounded-xl" />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 bg-bg-card rounded-xl" />
              ))}
            </div>
          </div>
        ) : accounts.length === 0 && !showForm ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4 opacity-20">&#x1f3e6;</div>
            <h2 className="text-2xl font-bold text-white mb-2">Add Your First Prop Account</h2>
            <p className="text-gray-400 mb-6">
              Track your prop firm rules, drawdown limits, and compliance in real time.
            </p>
            <button onClick={() => setShowForm(true)} className="btn-primary">
              Add Prop Account
            </button>
          </div>
        ) : (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-white">Prop Compliance</h1>
                {accounts.length > 1 && (
                  <div>
                    <label htmlFor="account-select" className="sr-only">Select account</label>
                    <select
                      id="account-select"
                      value={selectedId ?? ""}
                      onChange={(e) => setSelectedId(e.target.value)}
                      className="text-sm bg-bg-card border border-border rounded-lg px-3 py-1.5 text-gray-300"
                    >
                      {accounts.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.firm} — {a.phase} (${a.balance.toLocaleString()})
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <button
                onClick={() => setShowForm(!showForm)}
                className="text-xs text-accent hover:text-accent/80 transition-colors"
              >
                {showForm ? "Cancel" : "+ Add Account"}
              </button>
            </div>

            {showForm && (
              <form
                onSubmit={handleCreate}
                className="bg-bg-card rounded-xl border border-border p-6 mb-6 grid grid-cols-1 sm:grid-cols-4 gap-4 items-end"
              >
                <div>
                  <label htmlFor="firm" className="block text-xs text-gray-400 mb-1">Firm</label>
                  <select
                    id="firm"
                    value={formFirm}
                    onChange={(e) => setFormFirm(e.target.value)}
                    className="w-full text-sm bg-bg-primary border border-border rounded-lg px-3 py-2 text-gray-300"
                  >
                    {FIRM_PRESETS.map((f) => (
                      <option key={f} value={f}>{f}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="balance" className="block text-xs text-gray-400 mb-1">Balance</label>
                  <input
                    id="balance"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formBalance}
                    onChange={(e) => setFormBalance(e.target.value)}
                    placeholder="100000"
                    className="w-full text-sm bg-bg-primary border border-border rounded-lg px-3 py-2 text-gray-300"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="phase" className="block text-xs text-gray-400 mb-1">Phase</label>
                  <select
                    id="phase"
                    value={formPhase}
                    onChange={(e) => setFormPhase(e.target.value)}
                    className="w-full text-sm bg-bg-primary border border-border rounded-lg px-3 py-2 text-gray-300"
                  >
                    {PHASE_OPTIONS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn-primary text-sm py-2 disabled:opacity-50"
                >
                  {submitting ? "Creating..." : "Create Account"}
                </button>
              </form>
            )}

            {selectedAccount && (
              <>
                {complianceLoading ? (
                  <div className="animate-pulse space-y-4">
                    <div className="h-20 bg-bg-card rounded-xl" />
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-28 bg-bg-card rounded-xl" />
                      ))}
                    </div>
                  </div>
                ) : compliance ? (
                  <div className="space-y-6">
                    <div className="flex flex-col sm:flex-row gap-6 items-start">
                      <div
                        role="status"
                        className={`flex-1 rounded-xl border p-6 ${status!.bg} ${status!.border}`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs text-gray-500 mb-1">Account Status</p>
                            <p className={`text-3xl font-bold font-mono ${status!.text}`}>
                              {status!.label}
                            </p>
                            <p className="text-xs text-gray-500 mt-2">
                              {selectedAccount.firm} &middot; {selectedAccount.phase} &middot;{" "}
                              ${selectedAccount.balance.toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="bg-bg-card rounded-xl border border-border p-6">
                        <RiskGauge score={compliance.risk_score} />
                      </div>
                    </div>

                    <section aria-label="Compliance rules">
                      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                        Rule Tracking
                      </h2>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {compliance.rules.map((rule, i) => (
                          <RuleCard key={i} rule={rule} />
                        ))}
                      </div>
                    </section>

                    {compliance.warnings.length > 0 && (
                      <section aria-label="Warnings">
                        <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider mb-3">
                          Warnings
                        </h2>
                        <div className="space-y-2">
                          {compliance.warnings.map((w, i) => (
                            <div
                              key={i}
                              className={`rounded-lg border p-4 text-sm ${
                                w.level === "critical"
                                  ? "bg-red-500/5 border-red-500/20 text-red-400"
                                  : "bg-yellow-500/5 border-yellow-500/20 text-yellow-400"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <p>{w.message}</p>
                                <span className="text-[10px] text-gray-500 ml-4 whitespace-nowrap">
                                  {new Date(w.timestamp).toLocaleString()}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </section>
                    )}

                    {compliance.violations.length > 0 && (
                      <section aria-label="Violations" role="alert">
                        <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">
                          Violations
                        </h2>
                        <div className="space-y-2">
                          {compliance.violations.map((v, i) => (
                            <div
                              key={i}
                              className="bg-red-900/10 border border-red-600/30 rounded-lg p-4 text-sm text-red-400"
                            >
                              {v}
                            </div>
                          ))}
                        </div>
                      </section>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-10">
                    Unable to load compliance data.
                  </p>
                )}
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
