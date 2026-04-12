import { useEffect, useRef, memo } from "react";

interface Props {
  symbol?: string;
  height?: number;
}

function resolveSymbol(raw: string): string {
  if (raw.includes(":")) return raw;
  const upper = raw.toUpperCase();
  const forexPairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"];
  const metals = ["XAUUSD", "XAGUSD", "GOLD", "SILVER"];
  const oil = ["USOIL", "UKOIL", "WTICOUSD", "BCOUSD", "CRUDEOIL"];
  const crypto = ["BTCUSD", "ETHUSD", "BTCUSDT", "ETHUSDT"];
  if (forexPairs.includes(upper)) return `FX:${upper}`;
  if (metals.includes(upper)) return `OANDA:${upper}`;
  if (oil.includes(upper)) return `TVC:${upper}`;
  if (crypto.includes(upper)) return `BITSTAMP:${upper}`;
  if (upper === "NIFTY" || upper === "BANKNIFTY") return `NSE:${upper}`;
  return `NSE:${upper}`;
}

function LiveChartInner({ symbol = "NSE:NIFTY", height = 500 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.async = true;
    script.type = "text/javascript";
    const resolved = resolveSymbol(symbol);
    script.textContent = JSON.stringify({
      autosize: true,
      symbol: resolved,
      interval: "5",
      timezone: "Asia/Kolkata",
      theme: "dark",
      style: "1",
      locale: "en",
      backgroundColor: "#0a0a0f",
      gridColor: "rgba(30, 30, 46, 0.6)",
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false,
      calendar: false,
      hide_volume: false,
      support_host: "https://www.tradingview.com",
      enable_publishing: false,
      allow_symbol_change: true,
      studies: ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
    });

    containerRef.current.innerHTML = "";
    const widgetDiv = document.createElement("div");
    widgetDiv.className = "tradingview-widget-container__widget";
    widgetDiv.style.height = `${height}px`;
    widgetDiv.style.width = "100%";
    containerRef.current.appendChild(widgetDiv);
    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, [symbol, height]);

  return (
    <div className="card p-0 overflow-hidden">
      <div
        ref={containerRef}
        className="tradingview-widget-container"
        style={{ height: `${height}px`, width: "100%" }}
      />
    </div>
  );
}

export default memo(LiveChartInner);
