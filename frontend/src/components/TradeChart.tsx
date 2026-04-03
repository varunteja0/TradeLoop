import { useEffect, useRef, memo } from "react";
import { createChart, IChartApi, CandlestickData, Time } from "lightweight-charts";

interface TradeMarker {
  timestamp: string;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  pnl: number;
  duration_minutes: number | null;
}

interface Props {
  trades: TradeMarker[];
  symbol: string;
  height?: number;
}

function TradeChartInner({ trades, symbol, height = 400 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || trades.length === 0) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { color: "#12121a" },
        textColor: "#6b7280",
      },
      grid: {
        vertLines: { color: "#1e1e2e" },
        horzLines: { color: "#1e1e2e" },
      },
      crosshair: {
        mode: 0,
      },
      timeScale: {
        borderColor: "#1e1e2e",
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: "#1e1e2e",
      },
    });
    chartRef.current = chart;

    const symbolTrades = trades.filter(t => t.symbol === symbol);
    if (symbolTrades.length === 0) return;

    // Generate synthetic candlestick data around trade prices
    // until real OHLC data is available from broker API
    const sortedTrades = [...symbolTrades].sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    const candles: CandlestickData[] = [];
    const markers: { time: Time; position: string; color: string; shape: string; text: string }[] = [];

    for (const trade of sortedTrades) {
      const time = Math.floor(new Date(trade.timestamp).getTime() / 1000) as Time;
      const range = Math.abs(trade.exit_price - trade.entry_price);
      const noise = range * 0.3 || trade.entry_price * 0.002;

      candles.push({
        time,
        open: trade.entry_price,
        high: Math.max(trade.entry_price, trade.exit_price) + noise,
        low: Math.min(trade.entry_price, trade.exit_price) - noise,
        close: trade.exit_price,
      });

      markers.push({
        time,
        position: trade.side === "BUY" ? "belowBar" : "aboveBar",
        color: trade.pnl >= 0 ? "#00d4aa" : "#ff4757",
        shape: trade.side === "BUY" ? "arrowUp" : "arrowDown",
        text: `${trade.side} ${trade.pnl >= 0 ? "+" : ""}$${trade.pnl.toFixed(0)}`,
      });
    }

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#00d4aa",
      downColor: "#ff4757",
      borderUpColor: "#00d4aa",
      borderDownColor: "#ff4757",
      wickUpColor: "#00d4aa",
      wickDownColor: "#ff4757",
    });

    // Deduplicate candles by time (multiple trades at same timestamp)
    const uniqueCandles = new Map<number, CandlestickData>();
    for (const c of candles) {
      const t = c.time as number;
      if (!uniqueCandles.has(t)) {
        uniqueCandles.set(t, c);
      }
    }
    const sortedCandles = Array.from(uniqueCandles.values()).sort(
      (a, b) => (a.time as number) - (b.time as number)
    );

    if (sortedCandles.length > 0) {
      candleSeries.setData(sortedCandles);
      candleSeries.setMarkers(
        markers.sort((a, b) => (a.time as number) - (b.time as number)) as any
      );
    }

    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chart.applyOptions({ width: entry.contentRect.width });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [trades, symbol, height]);

  const tradeCount = trades.filter(t => t.symbol === symbol).length;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-300">
          Trade Chart — <span className="text-white font-mono">{symbol}</span>
        </h3>
        <span className="text-xs text-gray-500">{tradeCount} trades</span>
      </div>
      <div
        ref={containerRef}
        className="rounded-lg overflow-hidden"
        aria-label={`Price chart for ${symbol} with trade markers`}
      />
      {tradeCount === 0 && (
        <div className="text-center py-8 text-gray-500 text-sm">
          No trades for {symbol}
        </div>
      )}
    </div>
  );
}

export default memo(TradeChartInner);
