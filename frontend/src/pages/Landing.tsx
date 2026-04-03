import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../store/auth";
import Logo from "../components/Logo";

export default function Landing() {
  const user = useAuth((s) => s.user);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.title = "TradeLoop — Your Trades Tell a Story";
    const meta = document.querySelector('meta[name="description"]');
    if (meta) {
      meta.setAttribute(
        "content",
        "Upload your trade history. TradeLoop finds the patterns you can't see — revenge trades, best hours, worst setups, behavioral leaks."
      );
    }
  }, []);

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="relative flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <Logo linkTo="/" />

        <button
          className="sm:hidden text-gray-400 hover:text-white transition-colors"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={menuOpen}
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            role="img"
            aria-label="Menu icon"
          >
            {menuOpen ? (
              <>
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </button>

        <div className="hidden sm:flex items-center gap-4">
          {user ? (
            <Link to="/dashboard" className="btn-primary text-sm">
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-gray-400 hover:text-white transition-colors text-sm">
                Log in
              </Link>
              <Link to="/register" className="btn-primary text-sm">
                Get Started Free
              </Link>
            </>
          )}
        </div>

        {menuOpen && (
          <div className="absolute top-full left-0 right-0 bg-bg-primary border-b border-border px-6 py-4 flex flex-col gap-3 sm:hidden z-50">
            {user ? (
              <Link to="/dashboard" className="btn-primary text-sm text-center" onClick={() => setMenuOpen(false)}>
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-gray-400 hover:text-white transition-colors text-sm"
                  onClick={() => setMenuOpen(false)}
                >
                  Log in
                </Link>
                <Link to="/register" className="btn-primary text-sm text-center" onClick={() => setMenuOpen(false)}>
                  Get Started Free
                </Link>
              </>
            )}
          </div>
        )}
      </nav>

      <main>
        <section className="max-w-5xl mx-auto px-6 pt-24 pb-20 text-center">
          <div className="inline-block mb-6 px-4 py-1.5 rounded-full border border-border text-sm text-accent">
            Free for your first 50 trades/month
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold text-white leading-tight mb-6">
            Your Trades Tell a Story.
            <br />
            <span className="text-accent">Most Traders Never Read It.</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed">
            Upload your trade history. TradeLoop finds the patterns you can't see —
            revenge trades, best hours, worst setups, behavioral leaks — so you stop
            losing money to yourself.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register" className="btn-primary text-lg px-8 py-4 w-full sm:w-auto">
              Upload Your First Trades Free
            </Link>
            <a href="#features" className="btn-secondary text-lg px-8 py-4 w-full sm:w-auto">
              See How It Works
            </a>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 max-w-lg mx-auto mt-16">
            {[
            ["50+", "Metrics computed"],
            ["8", "Leak detectors with $ cost"],
            ["5", "Prop firm presets"],
            ].map(([val, label]) => (
              <div key={label}>
                <div className="text-2xl font-bold text-white">{val}</div>
                <div className="text-sm text-gray-500">{label}</div>
              </div>
            ))}
          </div>
        </section>

        <section id="features" className="max-w-6xl mx-auto px-6 py-20">
          <div className="grid md:grid-cols-3 gap-6">
            <FeatureCard
              icon={
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  role="img"
                  aria-label="Clock icon"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 6v6l4 2" />
                </svg>
              }
              title="Know Exactly What Your Leaks Cost"
              description="Not just 'you revenge traded 12 times.' We show you the EXACT dollar amount: 'Revenge trading cost you ₹47,230. Here's your equity curve without those trades.'"
            />
            <FeatureCard
              icon={
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  role="img"
                  aria-label="Warning icon"
                >
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              }
              title="Prop Firm Compliance"
              description="Real-time drawdown tracking for FTMO, FundingPips, The5ers. Know exactly how much room you have before a limit breach. Never blow a challenge again."
            />
            <FeatureCard
              icon={
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  role="img"
                  aria-label="Trend up icon"
                >
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                  <polyline points="17 6 23 6 23 12" />
                </svg>
              }
              title="Auto-Sync From Your Broker"
              description="Connect Zerodha or Angel One. Trades import automatically — no more CSV exports. See your analytics update in real-time as you trade."
            />
          </div>
        </section>

        {/* What makes us different */}
        <section className="max-w-6xl mx-auto px-6 py-20">
          <h2 className="text-3xl font-bold text-white text-center mb-4">
            Not Another Stats Dashboard.
          </h2>
          <p className="text-gray-400 text-center max-w-2xl mx-auto mb-12">
            Other tools show you numbers. TradeLoop shows you the exact dollar cost of every behavioral leak
            and what your equity curve would look like without them.
          </p>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="card border-accent/20 p-6">
              <div className="text-accent text-sm font-semibold uppercase tracking-wider mb-2">Counterfactual Insights</div>
              <h3 className="text-xl font-bold text-white mb-2">"Revenge trading cost you $47,230"</h3>
              <p className="text-gray-400 text-sm">Every behavioral pattern comes with the exact dollar impact, a what-if equity curve, and a specific recommendation. Not vague advice — math.</p>
            </div>
            <div className="card border-accent/20 p-6">
              <div className="text-accent text-sm font-semibold uppercase tracking-wider mb-2">Prop Firm Mode</div>
              <h3 className="text-xl font-bold text-white mb-2">Never Blow a Challenge Again</h3>
              <p className="text-gray-400 text-sm">Real-time drawdown tracking for FTMO, FundingPips, The5ers. See your daily loss limit, max drawdown, and consistency score — with alerts before you breach.</p>
            </div>
            <div className="card border-accent/20 p-6">
              <div className="text-accent text-sm font-semibold uppercase tracking-wider mb-2">Trades on Charts</div>
              <h3 className="text-xl font-bold text-white mb-2">See Your Entries on Price Action</h3>
              <p className="text-gray-400 text-sm">TradingView-powered candlestick charts with your trade markers. See exactly where you entered and exited, with P&L shading.</p>
            </div>
            <div className="card border-accent/20 p-6">
              <div className="text-accent text-sm font-semibold uppercase tracking-wider mb-2">Weekly Intelligence</div>
              <h3 className="text-xl font-bold text-white mb-2">Your Trading Report Card</h3>
              <p className="text-gray-400 text-sm">Every Sunday: a graded report with week-over-week comparison, top insights ranked by dollar impact, and one specific thing to fix next week.</p>
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="max-w-4xl mx-auto px-6 py-20">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Connect. Analyze. Improve.
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Connect", desc: "Link your Zerodha or Angel One account. Trades sync automatically. Or upload a CSV." },
              { step: "02", title: "Discover", desc: "See exactly where you're leaking money — with dollar amounts and what-if scenarios." },
              { step: "03", title: "Improve", desc: "Weekly grades, specific recommendations, and prop firm compliance tracking." },
            ].map((s) => (
              <div key={s.step} className="text-center">
                <div className="text-accent font-mono text-sm mb-2">{s.step}</div>
                <h3 className="text-xl font-bold text-white mb-2">{s.title}</h3>
                <p className="text-gray-400 text-sm">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Pricing */}
        <section className="max-w-5xl mx-auto px-6 py-20">
          <h2 className="text-3xl font-bold text-white text-center mb-12">Simple Pricing</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="card p-6 text-center">
              <div className="text-sm text-gray-500 uppercase mb-2">Free</div>
              <div className="text-3xl font-bold text-white mb-1">$0</div>
              <div className="text-sm text-gray-500 mb-6">50 trades/month</div>
              <ul className="text-sm text-gray-400 space-y-2 text-left mb-6">
                <li>CSV upload</li>
                <li>Basic analytics</li>
                <li>Behavioral detection</li>
              </ul>
              <Link to="/register" className="btn-secondary w-full block text-center">Get Started</Link>
            </div>
            <div className="card p-6 text-center border-accent/40 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-bg-primary text-xs font-bold px-3 py-1 rounded-full">POPULAR</div>
              <div className="text-sm text-accent uppercase mb-2">Pro</div>
              <div className="text-3xl font-bold text-white mb-1">$12<span className="text-lg text-gray-500">/mo</span></div>
              <div className="text-sm text-gray-500 mb-6">Unlimited trades</div>
              <ul className="text-sm text-gray-400 space-y-2 text-left mb-6">
                <li>Everything in Free</li>
                <li>Broker auto-sync</li>
                <li>Counterfactual insights</li>
                <li>Weekly intelligence reports</li>
                <li>Trade charts</li>
              </ul>
              <Link to="/register" className="btn-primary w-full block text-center">Start Free Trial</Link>
            </div>
            <div className="card p-6 text-center">
              <div className="text-sm text-gray-500 uppercase mb-2">Prop Trader</div>
              <div className="text-3xl font-bold text-white mb-1">$18<span className="text-lg text-gray-500">/mo</span></div>
              <div className="text-sm text-gray-500 mb-6">Multi-account</div>
              <ul className="text-sm text-gray-400 space-y-2 text-left mb-6">
                <li>Everything in Pro</li>
                <li>Prop firm compliance</li>
                <li>Real-time drawdown alerts</li>
                <li>Multi-account tracking</li>
                <li>Consistency rule monitor</li>
              </ul>
              <Link to="/register" className="btn-primary w-full block text-center">Start Free Trial</Link>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="max-w-4xl mx-auto px-6 py-20 text-center">
          <div className="card p-12 border-accent/20">
            <h2 className="text-3xl font-bold text-white mb-4">
              Stop guessing. Start knowing.
            </h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">
              Your next 50 trades analyzed free. See exactly where your money goes — and how to keep more of it.
            </p>
            <Link to="/register" className="btn-primary text-lg px-10 py-4">
              Start Free
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-gray-500">
          <span>TradeLoop &copy; {new Date().getFullYear()}</span>
          <span>Built for traders who want to get better.</span>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="card hover:border-accent/30 transition-colors duration-300">
      <div className="text-accent mb-4">{icon}</div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
    </div>
  );
}
