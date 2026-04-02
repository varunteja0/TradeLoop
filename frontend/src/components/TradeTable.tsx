import { useState, useEffect } from "react";
import api from "../api/client";

interface Trade {
  id: string;
  timestamp: string;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  duration_minutes: number | null;
  setup_type: string | null;
}

export default function TradeTable() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const perPage = 20;

  useEffect(() => {
    setLoading(true);
    api
      .get(`/trades?page=${page}&per_page=${perPage}`)
      .then(({ data }) => {
        setTrades(data.trades);
        setTotal(data.total);
      })
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="card overflow-x-auto">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300">
          Trade History
          <span className="ml-2 text-gray-500 font-normal">({total} total)</span>
        </h3>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : trades.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No trades yet. Upload a CSV to get started.</div>
      ) : (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-500 uppercase border-b border-border">
                <th className="text-left pb-3 pr-2">Date</th>
                <th className="text-left pb-3 px-2">Symbol</th>
                <th className="text-left pb-3 px-2">Side</th>
                <th className="text-right pb-3 px-2">Entry</th>
                <th className="text-right pb-3 px-2">Exit</th>
                <th className="text-right pb-3 px-2">Qty</th>
                <th className="text-right pb-3 px-2">P&L</th>
                <th className="text-left pb-3 pl-2 hidden md:table-cell">Setup</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id} className="border-b border-border/30 hover:bg-bg-hover transition-colors">
                  <td className="py-2 pr-2 text-gray-400 text-xs font-mono whitespace-nowrap">
                    {new Date(t.timestamp).toLocaleDateString("en-IN", {
                      month: "short",
                      day: "numeric",
                    })}{" "}
                    {new Date(t.timestamp).toLocaleTimeString("en-IN", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="py-2 px-2 font-mono font-medium text-white text-xs">{t.symbol}</td>
                  <td className="py-2 px-2">
                    <span
                      className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                        t.side === "BUY" ? "bg-win/15 text-win" : "bg-loss/15 text-loss"
                      }`}
                    >
                      {t.side}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-right font-mono text-xs text-gray-400">
                    {t.entry_price.toFixed(2)}
                  </td>
                  <td className="py-2 px-2 text-right font-mono text-xs text-gray-400">
                    {t.exit_price.toFixed(2)}
                  </td>
                  <td className="py-2 px-2 text-right font-mono text-xs text-gray-400">{t.quantity}</td>
                  <td
                    className={`py-2 px-2 text-right font-mono text-xs font-medium ${
                      t.pnl >= 0 ? "text-win" : "text-loss"
                    }`}
                  >
                    {t.pnl >= 0 ? "+" : ""}
                    {t.pnl.toFixed(2)}
                  </td>
                  <td className="py-2 pl-2 text-xs text-gray-500 hidden md:table-cell">
                    {t.setup_type || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-xs text-gray-500">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
