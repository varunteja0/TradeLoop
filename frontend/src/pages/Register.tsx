import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import Logo from "../components/Logo";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const register = useAuth((s) => s.register);
  const loading = useAuth((s) => s.loading);
  const user = useAuth((s) => s.user);
  const hydrated = useAuth((s) => s.hydrated);
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Sign Up — TradeLoop";
  }, []);

  useEffect(() => {
    if (hydrated && user) navigate("/dashboard", { replace: true });
  }, [hydrated, user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    try {
      await register(email, password, name || undefined);
      localStorage.setItem("tradeloop_registered_at", Date.now().toString());
      navigate("/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Registration failed";
      setError(msg);
    }
  };

  if (!hydrated) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <main className="w-full max-w-md">
        <div className="flex justify-center mb-8">
          <Logo linkTo="/" />
        </div>

        <div className="card">
          <h1 className="text-2xl font-bold text-white mb-2 text-center">Create your account</h1>
          <p className="text-gray-500 text-sm text-center mb-6">50 trades/month analyzed free</p>

          {error && (
            <div role="alert" className="bg-loss/10 border border-loss/30 text-loss text-sm rounded-lg p-3 mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="register-name" className="block text-sm text-gray-400 mb-1.5">
                Name
              </label>
              <input
                id="register-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-field"
                placeholder="Your name"
                autoComplete="name"
              />
            </div>
            <div>
              <label htmlFor="register-email" className="block text-sm text-gray-400 mb-1.5">
                Email
              </label>
              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </div>
            <div>
              <label htmlFor="register-password" className="block text-sm text-gray-400 mb-1.5">
                Password
              </label>
              <input
                id="register-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="Min 6 characters"
                required
                minLength={6}
                autoComplete="new-password"
              />
              <p className="text-xs text-gray-500 mt-1.5">
                Must be at least 6 characters. Use a mix of letters, numbers, and symbols for best security.
              </p>
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-accent hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
