import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { createChart, CandlestickData, Time } from "lightweight-charts";
import api from "../api/client";
import Logo from "../components/Logo";
import { useAuth } from "../store/auth";

interface ReplayData {
  trade: {
    id: string;
    symbol: string;
    side: string;
    entry_price: number;
    exit_price: number;
    entry_time: number;
    exit_time: number;
    pnl: number;
    quantity: number;
  };
  candles: Array<{
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  mfe: { price_move: number; dollar_value: number; description: string };
  mae: { price_move: number; dollar_value: number; description: string };
  post_exit: {
    max_move: number;
    money_left_on_table: number;
    description: string;
  };
}

export default function TradeReplay() {
  const { tradeId } = useParams<{ tradeId: string }>();
  const [data, setData] = useState<ReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const chartRef = useRef<HTMLDivElement>(null);
  const logout = useAuth((s) => s.logout);

  useEffect(() => {
    document.title = "Trade Replay — TradeLoop";
  }, []);

  useEffect(() => {
    if (!tradeId) return;
    api
      .get(`/market/replay/${tradeId}`)
      .then(({ data: d }) => setData(d))
      .catch((err) =>
        setError(err.response?.data?.detail || "Failed to load trade"),
      )
      .finally(() => setLoading(false));
  }, [tradeId]);

  useEffect(() => {
    if (!data || !chartRef.current) return;

    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 450,
      layout: {
        background: { color: "#0a0a0f" },
        textColor: "#6b7280",
      },
      grid: {
        vertLines: { color: "#1e1e2e" },
        horzLines: { color: "#1e1e2e" },
      },
      crosshair: { mode: 0 },
      timeScale: {
        borderColor: "#1e1e2e",
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: { borderColor: "#1e1e2e" },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#00d4aa",
      downColor: "#ff4757",
      borderUpColor: "#00d4aa",
      borderDownColor: "#ff4757",
      wickUpColor: "#00d4aa",
      wickDownColor: "#ff4757",
    });

    const candles: CandlestickData[] = data.candles.map((c) => ({
      time: c.time as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    candleSeries.setData(candles);

    const markers = [
      {
        time: data.trade.entry_time as Time,
        position:
          data.trade.side === "BUY"
            ? ("belowBar" as const)
            : ("aboveBar" as const),
        color: "#00d4aa",
        shape:
          data.trade.side === "BUY"
            ? ("arrowUp" as const)
            : ("arrowDown" as const),
        text: `${data.trade.side} @ ₹${data.trade.entry_price}`,
      },
      {
        time: data.trade.exit_time as Time,
        position:
          data.trade.side === "BUY"
            ? ("aboveBar" as const)
            : ("belowBar" as const),
        color: data.trade.pnl >= 0 ? "#00d4aa" : "#ff4757",
        shape:
          data.trade.side === "BUY"
            ? ("arrowDown" as const)
            : ("arrowUp" as const),
        text: `EXIT @ ₹${data.trade.exit_price} (${data.trade.pnl >= 0 ? "+" : ""}₹${data.trade.pnl})`,
      },
    ].sort((a, b) => (a.time as number) - (b.time as number));

    candleSeries.setMarkers(markers);

    candleSeries.createPriceLine({
      price: data.trade.entry_price,
      color: "#00d4aa",
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "Entry",
    });
    candleSeries.createPriceLine({
      price: data.trade.exit_price,
      color: data.trade.pnl >= 0 ? "#00d4aa" : "#ff4757",
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
      title: "Exit",
    });

    chart.timeScale().fitContent();

    const el = chartRef.current;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries)
        chart.applyOptions({ width: entry.contentRect.width });
    });
    observer.observe(el);

    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [data]);

  const t = data?.trade;
  const isWin = t && t.pnl >= 0;

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <Logo linkTo="/" size="sm" />
          <div className="flex items-center gap-3">
            <Link
              to="/dashboard"
              className="text-xs text-gray-400 hover:text-white"
            >
              Dashboard
            </Link>
            <button
              onClick={logout}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {loading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-8 w-48 bg-bg-card rounded" />
            <div className="h-[450px] bg-bg-card rounded-xl" />
            <div className="grid grid-cols-3 gap-4">
              <div className="h-32 bg-bg-card rounded-xl" />
              <div className="h-32 bg-bg-card rounded-xl" />
              <div className="h-32 bg-bg-card rounded-xl" />
            </div>
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-loss mb-4">{error}</p>
            <Link to="/dashboard" className="btn-primary">
              Back to Dashboard
            </Link>
          </div>
        ) : data && t ? (
          <>
            <div className="flex items-center gap-3 mb-4">
              <Link
                to="/dashboard"
                className="text-gray-500 hover:text-white text-sm"
              >
                &larr; Back
              </Link>
              <h1 className="text-xl font-bold text-white">
                Trade Replay —{" "}
                <span className="font-mono">{t.symbol}</span>
              </h1>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded ${t.side === "BUY" ? "bg-win/15 text-win" : "bg-loss/15 text-loss"}`}
              >
                {t.side}
              </span>
              <span
                className={`text-sm font-mono font-bold ${isWin ? "text-win" : "text-loss"}`}
              >
                {isWin ? "+" : ""}₹{t.pnl.toFixed(2)}
              </span>
            </div>

            <div className="card p-0 overflow-hidden mb-6">
              <div ref={chartRef} style={{ height: "450px" }} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="card">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-win text-lg">&#9650;</span>
                  <h3 className="text-sm font-semibold text-gray-300">
                    Max Favorable (MFE)
                  </h3>
                </div>
                <p className="text-2xl font-bold font-mono text-win">
                  ₹{data.mfe.dollar_value.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {data.mfe.description}
                </p>
              </div>

              <div className="card">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-loss text-lg">&#9660;</span>
                  <h3 className="text-sm font-semibold text-gray-300">
                    Max Adverse (MAE)
                  </h3>
                </div>
                <p className="text-2xl font-bold font-mono text-loss">
                  ₹{data.mae.dollar_value.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {data.mae.description}
                </p>
              </div>

              <div className="card border-accent/20">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-accent text-lg">&#9733;</span>
                  <h3 className="text-sm font-semibold text-gray-300">
                    Money Left on Table
                  </h3>
                </div>
                <p className="text-2xl font-bold font-mono text-accent">
                  ₹{data.post_exit.money_left_on_table.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {data.post_exit.description}
                </p>
              </div>
            </div>

            <div className="card">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                Trade Details
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Entry</span>
                  <p className="font-mono text-white">₹{t.entry_price}</p>
                </div>
                <div>
                  <span className="text-gray-500">Exit</span>
                  <p className="font-mono text-white">₹{t.exit_price}</p>
                </div>
                <div>
                  <span className="text-gray-500">Quantity</span>
                  <p className="font-mono text-white">{t.quantity}</p>
                </div>
                <div>
                  <span className="text-gray-500">P&L</span>
                  <p
                    className={`font-mono font-bold ${isWin ? "text-win" : "text-loss"}`}
                  >
                    {isWin ? "+" : ""}₹{t.pnl.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
