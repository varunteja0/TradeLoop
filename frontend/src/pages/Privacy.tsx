import { useEffect } from "react";
import { Link } from "react-router-dom";
import Logo from "../components/Logo";

export default function Privacy() {
  useEffect(() => {
    document.title = "Privacy Policy — TradeLoop";
  }, []);

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <Logo linkTo="/" />
        <Link to="/" className="text-gray-400 hover:text-white transition-colors text-sm">
          Back to Home
        </Link>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-16">
        <h1 className="text-4xl font-extrabold text-white mb-2">Privacy Policy</h1>
        <p className="text-gray-500 text-sm mb-12">Last updated: April 2026</p>

        <div className="space-y-10 text-gray-300 leading-relaxed">
          <section>
            <h2 className="text-xl font-bold text-white mb-3">1. What Data We Collect</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li><span className="text-gray-300">Account information:</span> email address, name, and a securely hashed password (we never store your password in plain text).</li>
              <li><span className="text-gray-300">Trade data:</span> trade history you upload via CSV or that syncs from connected brokers, including instrument, entry/exit prices, quantities, timestamps, and fees.</li>
              <li><span className="text-gray-300">Broker tokens:</span> API credentials for connected brokers are encrypted at rest using AES-256 and are only used to fetch your trade data on your behalf.</li>
              <li><span className="text-gray-300">Usage data:</span> basic analytics such as page views, feature usage, and session duration to improve the product.</li>
              <li><span className="text-gray-300">Payment information:</span> subscription billing is handled by our payment processor (Razorpay). We do not store your card details.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">2. How We Use Your Data</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li>Computing analytics, behavioral insights, and performance metrics from your trade history.</li>
              <li>Generating weekly reports and compliance monitoring for prop firm accounts.</li>
              <li>Sending transactional emails (welcome, password reset, compliance alerts, weekly reports).</li>
              <li>Improving TradeLoop's features and user experience.</li>
            </ul>
            <p className="mt-3 text-gray-400">
              We <span className="text-white font-semibold">never sell your data</span> to third parties. Your trade data is yours — we use it solely to provide you with analytics and insights.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">3. Data Retention</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li><span className="text-gray-300">Trade data:</span> stored until you manually delete it or delete your account.</li>
              <li><span className="text-gray-300">Account data:</span> retained until you request account deletion.</li>
              <li><span className="text-gray-300">Analytics & reports:</span> generated on demand from your trade data and not independently stored long-term.</li>
              <li>Upon account deletion, all your data is permanently removed within 30 days.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">4. Security Measures</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li><span className="text-gray-300">Encryption at rest:</span> broker API tokens are encrypted with AES-256. Passwords are hashed with bcrypt.</li>
              <li><span className="text-gray-300">Encryption in transit:</span> all communication uses HTTPS/TLS.</li>
              <li><span className="text-gray-300">Authentication:</span> JWT-based authentication with short-lived access tokens and secure refresh tokens.</li>
              <li><span className="text-gray-300">Rate limiting:</span> login, registration, and upload endpoints are rate-limited to prevent abuse.</li>
              <li><span className="text-gray-300">Infrastructure:</span> hosted on Railway (backend) and Vercel (frontend) with automatic security updates.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">5. Your Rights</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li><span className="text-gray-300">Access:</span> view all data we hold about you from your Settings page.</li>
              <li><span className="text-gray-300">Export:</span> download your complete trade data and analytics in CSV format at any time.</li>
              <li><span className="text-gray-300">Delete:</span> permanently delete your account and all associated data from the Settings page.</li>
              <li><span className="text-gray-300">Correct:</span> update your profile information at any time.</li>
              <li><span className="text-gray-300">Opt out:</span> unsubscribe from non-essential emails via email preferences.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">6. Cookies</h2>
            <p className="text-gray-400">
              We use essential cookies only — for authentication (JWT stored in memory/local storage) and session management. We do not use tracking cookies or third-party advertising cookies.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">7. Third-Party Services</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li><span className="text-gray-300">Razorpay:</span> payment processing (subject to Razorpay's privacy policy).</li>
              <li><span className="text-gray-300">Resend:</span> transactional email delivery.</li>
              <li><span className="text-gray-300">Sentry:</span> error tracking to improve application reliability (no personal trade data is sent).</li>
              <li><span className="text-gray-300">Broker APIs:</span> Zerodha, Angel One — used solely to fetch your trade data with your explicit authorization.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">8. Contact</h2>
            <p className="text-gray-400">
              For privacy-related questions, data requests, or concerns, contact us at{" "}
              <a href="mailto:privacy@tradeloop.io" className="text-accent hover:underline">
                privacy@tradeloop.io
              </a>.
            </p>
          </section>
        </div>
      </main>

      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-gray-500">
          <span>TradeLoop &copy; {new Date().getFullYear()}</span>
          <div className="flex gap-4">
            <span className="text-gray-400">Privacy Policy</span>
            <Link to="/terms" className="hover:text-white transition-colors">Terms of Service</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
