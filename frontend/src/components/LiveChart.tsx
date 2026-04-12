import { useEffect, useRef, memo, useCallback } from "react";

interface Props {
  symbol?: string;
  height?: number;
}

/** US names that must not default to NSE (common equities / ETFs). */
const US_MAJOR = new Set([
  "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC",
  "NFLX", "DIS", "SPY", "QQQ", "IWM", "DIA", "V", "MA", "JPM", "BAC", "WFC", "GS", "MS",
  "XOM", "CVX", "PG", "KO", "PEP", "WMT", "COST", "HD", "LOW", "NKE", "SBUX", "BA", "CAT",
  "PFE", "JNJ", "UNH", "ABBV", "LLY", "CRM", "ORCL", "CSCO", "ADBE", "PYPL", "UBER", "LYFT",
  "COIN", "MSTR", "PLTR", "SOFI", "RIVN", "LCID", "F", "GM",
]);

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
  if (upper === "NIFTY" || upper === "BANKNIFTY" || upper === "FINNIFTY" || upper === "MIDCPNIFTY") {
    return `NSE:${upper}`;
  }
  if (US_MAJOR.has(upper)) return `NASDAQ:${upper}`;
  return `NSE:${upper}`;
}

const DEFAULT_HEIGHT = 620;
const MIN_HEIGHT = 520;

function debounce(fn: () => void, ms: number) {
  let t: ReturnType<typeof setTimeout> | undefined;
  return () => {
    if (t) clearTimeout(t);
    t = setTimeout(fn, ms);
  };
}

function LiveChartInner({ symbol = "NSE:NIFTY", height = DEFAULT_HEIGHT }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const containerIdRef = useRef(`tv_chart_${Math.random().toString(36).slice(2)}`);

  const chartHeight = Math.max(height, MIN_HEIGHT);

  const mountWidget = useCallback(
    (el: HTMLDivElement, innerWidth: number) => {
      const w = Math.max(Math.floor(innerWidth), 320);
      const id = containerIdRef.current;
      const resolved = resolveSymbol(symbol);

      el.innerHTML = "";
      const widgetDiv = document.createElement("div");
      widgetDiv.id = id;
      widgetDiv.className = "tradingview-widget-container__widget";
      widgetDiv.style.width = "100%";
      widgetDiv.style.height = `${chartHeight}px`;
      widgetDiv.style.minHeight = `${chartHeight}px`;
      widgetDiv.style.boxSizing = "border-box";
      el.appendChild(widgetDiv);

      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
      script.async = true;
      script.type = "text/javascript";
      // Numeric width/height + container_id: reliable in embeds; autosize:true often measures 0px on first paint.
      script.textContent = JSON.stringify({
        autosize: false,
        width: w,
        height: chartHeight,
        container_id: id,
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
      });
      el.appendChild(script);
    },
    [symbol, chartHeight],
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const run = () => {
      const rect = el.getBoundingClientRect();
      const innerW = rect.width > 0 ? rect.width : el.clientWidth;
      if (innerW < 100) return;
      mountWidget(el, innerW);
    };

    run();

    const debounced = debounce(run, 120);
    const ro = new ResizeObserver(() => debounced());
    ro.observe(el);
    window.addEventListener("orientationchange", debounced);

    return () => {
      ro.disconnect();
      window.removeEventListener("orientationchange", debounced);
      el.innerHTML = "";
    };
  }, [mountWidget]);

  const resolved = resolveSymbol(symbol);
  const showNseNote = resolved.startsWith("NSE:");

  return (
    <div className="card p-0 overflow-hidden shrink-0">
      <div className="flex flex-col gap-1 px-4 pt-3 pb-1 border-b border-border/60">
        <h3 className="text-sm font-semibold text-gray-300">Live chart</h3>
        <p className="text-[11px] text-gray-500 leading-snug">
          {showNseNote ? (
            <>
              NSE symbols use delayed data in the free TradingView embed. If you see “only available on TradingView,” open
              the full site from the widget — licensing limits the embed, not TradeLoop.
            </>
          ) : (
            <>Add indicators from the chart toolbar. Many panes in a short box will look squashed — give the chart enough height or remove extras.</>
          )}
        </p>
      </div>
      <div
        ref={containerRef}
        className="tradingview-widget-container w-full live-chart-host"
        style={{
          height: `${chartHeight}px`,
          minHeight: `${chartHeight}px`,
          width: "100%",
        }}
      />
    </div>
  );
}

export default memo(LiveChartInner);
