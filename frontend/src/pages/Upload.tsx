import { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../store/auth";
import Logo from "../components/Logo";
import { useToast } from "../components/Toast";

export default function Upload() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ imported: number; skipped: number; errors: string[] } | null>(null);
  const [error, setError] = useState("");
  const [broker, setBroker] = useState("auto");
  const navigate = useNavigate();
  const logout = useAuth((s) => s.logout);
  const { toast } = useToast();

  useEffect(() => {
    document.title = "Upload Trades — TradeLoop";
  }, []);

  const onDrop = useCallback(
    async (files: File[]) => {
      if (!files.length) return;
      setUploading(true);
      setError("");
      setResult(null);

      const formData = new FormData();
      formData.append("file", files[0]);

      try {
        const { data } = await api.post(`/trades/upload?broker=${broker}`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setResult(data);
        toast(`${data.imported} trades imported successfully!`, "success");
        setTimeout(() => navigate("/dashboard"), 1500);
      } catch (err: unknown) {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          "Upload failed";
        setError(msg);
      } finally {
        setUploading(false);
      }
    },
    [broker, toast]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="flex items-center justify-between px-6 py-4 max-w-5xl mx-auto">
        <Logo linkTo="/" />
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="text-sm text-gray-400 hover:text-white transition-colors">
            Dashboard
          </Link>
          <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-300 transition-colors">
            Log out
          </button>
        </div>
      </nav>

      <main className="max-w-2xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-bold text-white mb-2">Upload Trades</h1>
        <p className="text-gray-400 mb-8">
          Drop your CSV trade export. We support Zerodha, MT4/MT5, and generic formats.
        </p>

        <div className="mb-6">
          <label htmlFor="broker-select" className="block text-sm text-gray-400 mb-2">
            Broker Format
          </label>
          <div id="broker-select" className="flex flex-wrap gap-2" role="radiogroup" aria-label="Broker format selection">
            {["auto", "generic", "zerodha", "mt4"].map((b) => (
              <button
                key={b}
                onClick={() => setBroker(b)}
                role="radio"
                aria-checked={broker === b}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  broker === b
                    ? "bg-accent text-bg-primary"
                    : "bg-bg-card border border-border text-gray-400 hover:text-white"
                }`}
              >
                {b === "auto" ? "Auto-detect" : b === "mt4" ? "MT4/MT5" : b.charAt(0).toUpperCase() + b.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div
          {...getRootProps()}
          aria-label="CSV file upload dropzone. Drag and drop or click to browse."
          className={`card border-2 border-dashed cursor-pointer transition-all duration-200 text-center py-16 ${
            isDragActive
              ? "border-accent bg-accent/5"
              : uploading
              ? "border-gray-600 opacity-50"
              : "border-border hover:border-accent/50"
          }`}
        >
          <input {...getInputProps()} />
          <div className="text-gray-400">
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                <span>Processing your trades...</span>
              </div>
            ) : isDragActive ? (
              <p className="text-accent text-lg">Drop your CSV here</p>
            ) : (
              <>
                <svg
                  className="w-12 h-12 mx-auto mb-4 text-gray-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  role="img"
                  aria-label="Upload icon"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
                  />
                </svg>
                <p className="text-lg mb-2">Drag and drop your CSV file here</p>
                <p className="text-sm text-gray-500">or click to browse</p>
              </>
            )}
          </div>
        </div>

        {error && (
          <div role="alert" className="mt-6 bg-loss/10 border border-loss/30 text-loss rounded-lg p-4">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-6 card border-accent/30">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-accent"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                  role="img"
                  aria-label="Success checkmark"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <div className="text-white font-semibold">{result.imported} trades imported</div>
                {result.skipped > 0 && (
                  <div className="text-sm text-gray-400">{result.skipped} skipped</div>
                )}
              </div>
            </div>
            <button onClick={() => navigate("/dashboard")} className="btn-primary w-full">
              View Your Analytics
            </button>
          </div>
        )}

        <div className="mt-8 card">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Expected CSV Format</h3>
          <code className="text-xs text-gray-500 font-mono block overflow-x-auto">
            date,symbol,side,entry_price,exit_price,quantity,pnl,duration,setup,notes,fees
          </code>
          <p className="text-xs text-gray-500 mt-3">
            Or just export from your broker — we&apos;ll auto-detect Zerodha and MT4/MT5 formats.
          </p>
        </div>
      </main>
    </div>
  );
}
