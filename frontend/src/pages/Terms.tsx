import { useEffect } from "react";
import { Link } from "react-router-dom";
import Logo from "../components/Logo";

export default function Terms() {
  useEffect(() => {
    document.title = "Terms of Service — TradeLoop";
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
        <h1 className="text-4xl font-extrabold text-white mb-2">Terms of Service</h1>
        <p className="text-gray-500 text-sm mb-12">Last updated: April 2026</p>

        <div className="space-y-10 text-gray-300 leading-relaxed">
          <section>
            <h2 className="text-xl font-bold text-white mb-3">1. Service Description</h2>
            <p className="text-gray-400">
              TradeLoop is a trading analytics platform that helps traders understand their behavioral patterns,
              identify performance leaks, and track prop firm compliance. We provide analytics, insights,
              and reports based on trade data you upload or sync from supported brokers.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">2. User Responsibilities</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li>You must provide accurate and truthful information when creating your account.</li>
              <li>You are responsible for maintaining the security of your account credentials.</li>
              <li>You must not upload manipulated, fabricated, or misleading trade data.</li>
              <li>You must not use the service to circumvent prop firm rules or misrepresent your trading performance.</li>
              <li>You must not attempt to reverse-engineer, scrape, or abuse the platform's APIs.</li>
              <li>You must comply with all applicable laws and regulations in your jurisdiction.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">3. Not Financial Advice</h2>
            <p className="text-gray-400">
              TradeLoop is an <span className="text-white font-semibold">analytics and educational tool</span>.
              Nothing on this platform constitutes financial advice, investment recommendations, or trading signals.
              All analytics, insights, grades, and reports are provided for informational and educational purposes only.
              You are solely responsible for your trading decisions. Past performance patterns identified by TradeLoop
              do not guarantee future results.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">4. Limitation of Liability</h2>
            <p className="text-gray-400">
              TradeLoop is provided "as is" without warranties of any kind, express or implied. We do not guarantee
              the accuracy, completeness, or reliability of any analytics or insights generated from your data.
              In no event shall TradeLoop, its founders, employees, or affiliates be liable for any indirect,
              incidental, special, consequential, or punitive damages, including but not limited to loss of profits
              or trading losses, arising from your use of the service.
            </p>
            <p className="text-gray-400 mt-3">
              Our total liability for any claim arising from these terms or your use of the service shall not
              exceed the amount you paid us in the 12 months preceding the claim.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">5. Payment Terms</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li><span className="text-gray-300">Free tier:</span> 50 trades per month with basic analytics at no cost.</li>
              <li><span className="text-gray-300">Billing:</span> paid plans are billed monthly. Payment is processed securely via Razorpay.</li>
              <li><span className="text-gray-300">Cancellation:</span> you may cancel your subscription at any time from the Settings page. Your plan remains active until the end of the current billing period.</li>
              <li><span className="text-gray-300">Refunds:</span> we offer a full refund within 7 days of your first paid subscription. After that, no refunds are provided for partial billing periods.</li>
              <li><span className="text-gray-300">Price changes:</span> we will notify you at least 30 days before any price increase. You may cancel before the new pricing takes effect.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">6. Intellectual Property</h2>
            <p className="text-gray-400">
              The TradeLoop platform, including its design, code, algorithms, analytics engine, and branding,
              is the intellectual property of TradeLoop. You retain full ownership of your trade data.
              By using the service, you grant us a limited license to process your data solely for the purpose
              of providing analytics and insights to you.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">7. Account Termination</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-400">
              <li><span className="text-gray-300">By you:</span> you may delete your account at any time from the Settings page. All your data will be permanently removed within 30 days.</li>
              <li><span className="text-gray-300">By us:</span> we reserve the right to suspend or terminate accounts that violate these terms, abuse the platform, or engage in fraudulent activity. We will provide notice and an opportunity to export your data when possible.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">8. Data & Privacy</h2>
            <p className="text-gray-400">
              Your use of TradeLoop is also governed by our{" "}
              <Link to="/privacy" className="text-accent hover:underline">Privacy Policy</Link>,
              which describes how we collect, use, and protect your data.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">9. Changes to Terms</h2>
            <p className="text-gray-400">
              We may update these terms from time to time. Material changes will be communicated via email
              or an in-app notification at least 14 days before taking effect. Continued use of the service
              after changes take effect constitutes acceptance of the updated terms.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">10. Contact</h2>
            <p className="text-gray-400">
              For questions about these terms, contact us at{" "}
              <a href="mailto:legal@tradeloop.io" className="text-accent hover:underline">
                legal@tradeloop.io
              </a>.
            </p>
          </section>
        </div>
      </main>

      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-gray-500">
          <span>TradeLoop &copy; {new Date().getFullYear()}</span>
          <div className="flex gap-4">
            <Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
            <span className="text-gray-400">Terms of Service</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
