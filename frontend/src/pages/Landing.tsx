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
              ["Pure Math", "No AI guessing"],
              ["< 2 sec", "Full analysis"],
              ["11+", "Pattern types"],
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
              title="Know Your Edge"
              description="Which setups actually work? Which hours are profitable? Which symbols are bleeding you? Stop guessing, start knowing."
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
              title="Catch Your Leaks"
              description="Revenge trading detection, tilt alerts, overtrading days, sizing errors after losses. The patterns that cost you money."
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
              title="Track Your Progress"
              description="Equity curve, rolling metrics, streak analysis, risk ratios. Watch yourself improve over weeks and months."
            />
          </div>
        </section>

        <section className="max-w-4xl mx-auto px-6 py-20">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Three Steps. Two Minutes. Zero Guesswork.
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Upload", desc: "Export your trades from Zerodha, MT4, or any broker. Drop the CSV." },
              { step: "02", title: "Analyze", desc: "TradeLoop crunches every trade through 50+ metrics and pattern detectors." },
              { step: "03", title: "Improve", desc: "See exactly where you're leaking money. Fix it tomorrow morning." },
            ].map((s) => (
              <div key={s.step} className="text-center">
                <div className="text-accent font-mono text-sm mb-2">{s.step}</div>
                <h3 className="text-xl font-bold text-white mb-2">{s.title}</h3>
                <p className="text-gray-400 text-sm">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="max-w-4xl mx-auto px-6 py-20 text-center">
          <div className="card p-12 border-accent/20">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to read your trading story?
            </h2>
            <p className="text-gray-400 mb-8 max-w-lg mx-auto">
              50 trades/month analyzed free. No credit card needed. See your patterns in under 2 minutes.
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
