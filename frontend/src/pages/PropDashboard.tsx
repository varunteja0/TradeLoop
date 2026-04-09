import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import Logo from "../components/Logo";
import { useAuth } from "../store/auth";

interface PropAccount {
  id: string;
  name: string;
  firm: string;
  phase: string;
  initial_balance: number;
  is_active: boolean;
  status: string;
}

interface RuleStatus {
  rule_name: string;
  limit: number;
  current: number;
  remaining: number;
  usage_pct: number;
  status: string;
  message: string;
}

interface ComplianceData {
  overall_status: string;
  risk_score: number;
  all_rules: RuleStatus[];
  warnings: RuleStatus[];
  critical_warnings: RuleStatus[];
  violations: RuleStatus[];
  summary: string;
  current_balance: number;
  daily_pnl: number;
  daily_loss_remaining: number;
  max_drawdown_used: number;
  max_drawdown_remaining: number;
  profit_target_progress: number | null;
  trading_days_count: number;
  min_trading_days_met: boolean;
}

const FIRM_OPTIONS = [
  { value: "ftmo", label: "FTMO" },
  { value: "fundingpips", label: "FundingPips" },
  { value: "myforexfunds", label: "MyForexFunds" },
  { value: "the5ers", label: "The5ers" },
  { value: "topstep", label: "TopStep" },
  { value: "custom", label: "Other" },
];
const PHASE_OPTIONS = [
  { value: "challenge", label: "Challenge" },
  { value: "funded", label: "Funded" },
];

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string; border: string }> = {
  safe: { bg: "bg-emerald-500/10", text: "text-emerald-400", label: "SAFE", border: "border-emerald-500/30" },
  warning: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "WARNING", border: "border-yellow-500/30" },
  critical: { bg: "bg-red-500/10", text: "text-red-400", label: "CRITICAL", border: "border-red-500/30" },
  violated: { bg: "bg-red-900/20", text: "text-red-500", label: "VIOLATED", border: "border-red-600/50" },
};

function ruleBarColor(status: string, usage_pct: number): string {
  if (status === "violated") return "bg-red-500";
  if (status === "critical") return "bg-red-500";
  if (status === "warning") return "bg-yellow-500";
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
        <path d="M 10 75 A 60 60 0 0 1 130 75" fill="none" stroke="#1e1e2e" strokeWidth="10" strokeLinecap="round" />
        <path d="M 10 75 A 60 60 0 0 1 130 75" fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset} style={{ transition: "stroke-dashoffset 0.8s ease" }} />
      </svg>
      <p className="text-3xl font-bold font-mono text-white -mt-4">{score}</p>
      <p className="text-xs text-gray-500 mt-1">Risk Score</p>
    </div>
  );
}

function RuleCard({ rule }: { rule: RuleStatus }) {
  const pct = Math.min(rule.usage_pct, 100);
  const barColor = ruleBarColor(rule.status, pct);

  return (
    <div className="bg-bg-card rounded-xl border border-border p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-300">{rule.rule_name}</h3>
        {rule.status === "violated" && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">VIOLATED</span>
        )}
        {rule.status === "critical" && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">CRITICAL</span>
        )}
        {rule.status === "warning" && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-500">WARNING</span>
        )}
      </div>

      <div className="w-full h-2 bg-bg-hover rounded-full overflow-hidden mb-2"
        role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
        aria-label={`${rule.rule_name}: ${pct.toFixed(0)}%`}>
        <div className={`h-full rounded-full transition-all duration-500 ${barColor}`} style={{ width: `${pct}%` }} />
      </div>

      <div className="flex justify-between text-xs">
        <span className="text-gray-400">{pct.toFixed(1)}% used</span>
        <span className="text-gray-500">{rule.remaining.toFixed(2)} remaining</span>
      </div>
      <p className="text-[10px] text-gray-500 mt-2">{rule.message}</p>
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
  const [formFirm, setFormFirm] = useState(FIRM_OPTIONS[0].value);
  const [formBalance, setFormBalance] = useState("");
  const [formPhase, setFormPhase] = useState(PHASE_OPTIONS[0].value);
  const [formName, setFormName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);

  useEffect(() => {
    document.title = "Prop Compliance — TradeLoop";
  }, []);

  useEffect(() => {
    api.get("/prop")
      .then(({ data }) => {
        setAccounts(data);
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .catch((err) => {
        setError(err?.response?.data?.detail || "Failed to load prop accounts. Please try again.");
      })
      .finally(() => setLoading(false));
  }, []);

  const loadCompliance = useCallback((id: string) => {
    setComplianceLoading(true);
    setError("");
    api.get(`/prop/${id}/compliance`)
      .then(({ data }) => setCompliance(data))
      .catch((err) => {
        setCompliance(null);
        setError(err?.response?.data?.detail || "Failed to load compliance data.");
      })
      .finally(() => setComplianceLoading(false));
  }, []);

  useEffect(() => {
    if (selectedId) loadCompliance(selectedId);
  }, [selectedId, loadCompliance]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formBalance || submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const firmLabel = FIRM_OPTIONS.find((f) => f.value === formFirm)?.label ?? formFirm;
      const phaseLabel = PHASE_OPTIONS.find((p) => p.value === formPhase)?.label ?? formPhase;
      const { data } = await api.post("/prop", {
        name: formName || `${firmLabel} ${phaseLabel}`,
        firm: formFirm,
        initial_balance: parseFloat(formBalance),
        phase: formPhase,
      });
      setAccounts((prev) => [...prev, data]);
      setSelectedId(data.id);
      setShowForm(false);
      setFormBalance("");
      setFormName("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create account");
    } finally {
      setSubmitting(false);
    }
  }

  const selectedAccount = accounts.find((a) => a.id === selectedId);
  const statusStyle = compliance ? STATUS_STYLES[compliance.overall_status] ?? STATUS_STYLES.safe : null;

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 hidden sm:block">{user?.email}</span>
            <Link to="/dashboard" className="text-xs text-gray-400 hover:text-white transition-colors">Dashboard</Link>
            <button onClick={logout} className="text-xs text-gray-500 hover:text-gray-300">Log out</button>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {loading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-10 w-64 bg-bg-card rounded" />
            <div className="h-40 bg-bg-card rounded-xl" />
          </div>
        ) : accounts.length === 0 && !showForm ? (
          <div className="text-center py-20">
            <div className="text-5xl mb-4 opacity-30">&#x1f3e6;</div>
            <h2 className="text-2xl font-bold text-white mb-2">Add Your First Prop Account</h2>
            <p className="text-gray-400 mb-6">Track your prop firm rules, drawdown limits, and compliance in real time.</p>
            <button onClick={() => setShowForm(true)} className="btn-primary">Add Prop Account</button>
          </div>
        ) : (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-white">Prop Compliance</h1>
                {accounts.length > 1 && (
                  <div>
                    <label htmlFor="account-select" className="sr-only">Select account</label>
                    <select id="account-select" value={selectedId ?? ""}
                      onChange={(e) => setSelectedId(e.target.value)}
                      className="text-sm bg-bg-card border border-border rounded-lg px-3 py-1.5 text-gray-300">
                      {accounts.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name} — ₹{a.initial_balance.toLocaleString()}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <button onClick={() => setShowForm(!showForm)}
                className="text-xs text-accent hover:text-accent/80 transition-colors">
                {showForm ? "Cancel" : "+ Add Account"}
              </button>
            </div>

            {showForm && (
              <form onSubmit={handleCreate}
                className="bg-bg-card rounded-xl border border-border p-6 mb-6 space-y-4">
                {error && <div className="text-sm text-loss bg-loss/10 border border-loss/30 rounded-lg p-3" role="alert">{error}</div>}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="prop-name" className="block text-xs text-gray-400 mb-1">Account Name</label>
                    <input id="prop-name" type="text" value={formName} onChange={(e) => setFormName(e.target.value)}
                      placeholder="e.g. FTMO 100k Challenge #2" className="input-field text-sm" />
                  </div>
                  <div>
                    <label htmlFor="prop-firm" className="block text-xs text-gray-400 mb-1">Firm</label>
                    <select id="prop-firm" value={formFirm} onChange={(e) => setFormFirm(e.target.value)}
                      className="input-field text-sm">
                      {FIRM_OPTIONS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="prop-balance" className="block text-xs text-gray-400 mb-1">Initial Balance (₹)</label>
                    <input id="prop-balance" type="number" step="0.01" min="0" value={formBalance}
                      onChange={(e) => setFormBalance(e.target.value)} placeholder="100000"
                      className="input-field text-sm" required />
                  </div>
                  <div>
                    <label htmlFor="prop-phase" className="block text-xs text-gray-400 mb-1">Phase</label>
                    <select id="prop-phase" value={formPhase} onChange={(e) => setFormPhase(e.target.value)}
                      className="input-field text-sm">
                      {PHASE_OPTIONS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                    </select>
                  </div>
                </div>
                <button type="submit" disabled={submitting} className="btn-primary text-sm py-2 px-6 disabled:opacity-50">
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
                      {[1, 2, 3].map((i) => <div key={i} className="h-28 bg-bg-card rounded-xl" />)}
                    </div>
                  </div>
                ) : compliance ? (
                  <div className="space-y-6">
                    <div className="flex flex-col sm:flex-row gap-6 items-start">
                      <div role="status" className={`flex-1 rounded-xl border p-6 ${statusStyle!.bg} ${statusStyle!.border}`}>
                        <p className="text-xs text-gray-500 mb-1">Account Status</p>
                        <p className={`text-3xl font-bold font-mono ${statusStyle!.text}`}>{statusStyle!.label}</p>
                        <p className="text-xs text-gray-500 mt-2">
                          {selectedAccount.name} &middot; Balance: ₹{compliance.current_balance.toLocaleString()}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">{compliance.summary}</p>
                      </div>
                      <div className="bg-bg-card rounded-xl border border-border p-6">
                        <RiskGauge score={compliance.risk_score} />
                      </div>
                    </div>

                    {/* Key numbers */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="card">
                        <p className="text-xs text-gray-500">Today's P&L</p>
                        <p className={`text-lg font-bold font-mono ${compliance.daily_pnl >= 0 ? "text-win" : "text-loss"}`}>
                          {compliance.daily_pnl >= 0 ? "+" : ""}₹{compliance.daily_pnl.toFixed(2)}
                        </p>
                      </div>
                      <div className="card">
                        <p className="text-xs text-gray-500">Daily Loss Left</p>
                        <p className="text-lg font-bold font-mono text-white">₹{compliance.daily_loss_remaining.toFixed(2)}</p>
                      </div>
                      <div className="card">
                        <p className="text-xs text-gray-500">Drawdown Left</p>
                        <p className="text-lg font-bold font-mono text-white">₹{compliance.max_drawdown_remaining.toFixed(2)}</p>
                      </div>
                      <div className="card">
                        <p className="text-xs text-gray-500">Trading Days</p>
                        <p className="text-lg font-bold font-mono text-white">
                          {compliance.trading_days_count}
                          {compliance.min_trading_days_met ? " ✓" : ""}
                        </p>
                      </div>
                    </div>

                    <section aria-label="Compliance rules">
                      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Rule Tracking</h2>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {compliance.all_rules.map((rule, i) => <RuleCard key={i} rule={rule} />)}
                      </div>
                    </section>

                    {(compliance.critical_warnings.length > 0 || compliance.warnings.length > 0) && (
                      <section aria-label="Warnings">
                        <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider mb-3">Warnings</h2>
                        <div className="space-y-2">
                          {[...compliance.critical_warnings, ...compliance.warnings].map((w, i) => (
                            <div key={i} className={`rounded-lg border p-4 text-sm ${
                              w.status === "critical" ? "bg-red-500/5 border-red-500/20 text-red-400"
                                : "bg-yellow-500/5 border-yellow-500/20 text-yellow-400"}`}>
                              <p><strong>{w.rule_name}:</strong> {w.message}</p>
                            </div>
                          ))}
                        </div>
                      </section>
                    )}

                    {compliance.violations.length > 0 && (
                      <section aria-label="Violations" role="alert">
                        <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">Violations</h2>
                        <div className="space-y-2">
                          {compliance.violations.map((v, i) => (
                            <div key={i} className="bg-red-900/10 border border-red-600/30 rounded-lg p-4 text-sm text-red-400">
                              <strong>{v.rule_name}:</strong> {v.message}
                            </div>
                          ))}
                        </div>
                      </section>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-10">Unable to load compliance data.</p>
                )}
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
