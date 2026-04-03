import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../store/auth";
import Logo from "../components/Logo";

export default function NotFound() {
  const user = useAuth((s) => s.user);

  useEffect(() => {
    document.title = "Page Not Found — TradeLoop";
  }, []);

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <main className="text-center max-w-md">
        <div className="flex justify-center mb-8">
          <Logo linkTo="/" />
        </div>

        <h1 className="text-6xl font-extrabold text-white mb-4">404</h1>
        <p className="text-xl text-gray-400 mb-2">Page not found</p>
        <p className="text-sm text-gray-500 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link to={user ? "/dashboard" : "/"} className="btn-primary text-sm px-6 py-2.5 w-full sm:w-auto">
            {user ? "Go to Dashboard" : "Go Home"}
          </Link>
          {user && (
            <Link to="/upload" className="btn-secondary text-sm px-6 py-2.5 w-full sm:w-auto">
              Upload Trades
            </Link>
          )}
        </div>
      </main>
    </div>
  );
}
