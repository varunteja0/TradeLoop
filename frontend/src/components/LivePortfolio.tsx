import { useState, useEffect, memo } from "react";

interface Position {
  symbol: string;
  side: string;
  entry_price: number;
  current_price: number;
  quantity: number;
  pnl: number;
  change_pct: number;
}

function LivePortfolioInner() {
  const [clock, setClock] = useState(new Date());
  const [positions] = useState<Position[]>([
    { symbol: "NIFTY50", side: "BUY", entry_price: 22150, current_price: 22287, quantity: 2, pnl: 274, change_pct: 0.62 },
    { symbol: "BANKNIFTY", side: "BUY", entry_price: 47800, current_price: 47950, quantity: 1, pnl: 150, change_pct: 0.31 },
    { symbol: "RELIANCE", side: "SELL", entry_price: 2485, current_price: 2471, quantity: 10, pnl: 140, change_pct: 0.56 },
  ]);

  useEffect(() => {
    const timer = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const totalPnl = positions.reduce((sum, p) => sum + p.pnl, 0);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300">Live Positions</h3>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-win rounded-full animate-pulse" />
          <span className="text-xs text-gray-500 font-mono">
            {clock.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
          </span>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {positions.map((p) => (
          <div key={p.symbol} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
            <div className="flex items-center gap-3">
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                p.side === "BUY" ? "bg-win/15 text-win" : "bg-loss/15 text-loss"
              }`}>{p.side}</span>
              <div>
                <p className="text-sm font-mono font-medium text-white">{p.symbol}</p>
                <p className="text-[10px] text-gray-500">{p.quantity} qty @ {p.entry_price.toFixed(2)}</p>
              </div>
            </div>
            <div className="text-right">
              <p className={`text-sm font-mono font-bold ${p.pnl >= 0 ? "text-win" : "text-loss"}`}>
                {p.pnl >= 0 ? "+" : ""}{p.pnl.toFixed(2)}
              </p>
              <p className={`text-[10px] font-mono ${p.change_pct >= 0 ? "text-win" : "text-loss"}`}>
                {p.change_pct >= 0 ? "▲" : "▼"} {Math.abs(p.change_pct).toFixed(2)}%
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-border">
        <span className="text-xs text-gray-500">Total Unrealized P&L</span>
        <span className={`text-lg font-bold font-mono ${totalPnl >= 0 ? "text-win" : "text-loss"}`}>
          {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)}
        </span>
      </div>

      <p className="text-[10px] text-gray-600 mt-3 text-center">
        Connect your broker for live positions • <a href="/connect" className="text-accent hover:underline">Connect Now</a>
      </p>
    </div>
  );
}

export default memo(LivePortfolioInner);
