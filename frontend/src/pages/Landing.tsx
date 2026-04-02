import { Link } from "react-router-dom";
import { useAuth } from "../store/auth";

export default function Landing() {
  const user = useAuth((s) => s.user);

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0a0a0f" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </div>
          <span className="text-xl font-bold text-white">TradeLoop</span>
        </div>
        <div className="flex items-center gap-4">
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
      </nav>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-block mb-6 px-4 py-1.5 rounded-full border border-border text-sm text-accent">
          Free for your first 50 trades/month
        </div>
        <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold text-white leading-tight mb-6">
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
          <Link to="/register" className="btn-primary text-lg px-8 py-4">
            Upload Your First Trades Free
          </Link>
          <a href="#features" className="btn-secondary text-lg px-8 py-4">
            See How It Works
          </a>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-8 max-w-lg mx-auto mt-16">
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

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-20">
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
              </svg>
            }
            title="Know Your Edge"
            description="Which setups actually work? Which hours are profitable? Which symbols are bleeding you? Stop guessing, start knowing."
          />
          <FeatureCard
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            }
            title="Catch Your Leaks"
            description="Revenge trading detection, tilt alerts, overtrading days, sizing errors after losses. The patterns that cost you money."
          />
          <FeatureCard
            icon={
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                <polyline points="17 6 23 6 23 12" />
              </svg>
            }
            title="Track Your Progress"
            description="Equity curve, rolling metrics, streak analysis, risk ratios. Watch yourself improve over weeks and months."
          />
        </div>
      </section>

      {/* How it works */}
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

      {/* CTA */}
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

      {/* Footer */}
      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-gray-500">
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
