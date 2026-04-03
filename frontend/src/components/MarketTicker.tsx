import { useEffect, useRef, memo } from "react";

function MarketTickerInner() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js";
    script.async = true;
    script.type = "text/javascript";
    script.textContent = JSON.stringify({
      symbols: [
        { proName: "NSE:NIFTY", title: "NIFTY 50" },
        { proName: "NSE:BANKNIFTY", title: "BANK NIFTY" },
        { proName: "NSE:RELIANCE", title: "RELIANCE" },
        { proName: "NSE:TCS", title: "TCS" },
        { proName: "NSE:HDFCBANK", title: "HDFC BANK" },
        { proName: "NSE:INFY", title: "INFOSYS" },
        { proName: "NSE:SBIN", title: "SBI" },
        { proName: "FX:EURUSD", title: "EUR/USD" },
        { proName: "FX:GBPUSD", title: "GBP/USD" },
        { proName: "BITSTAMP:BTCUSD", title: "BTC/USD" },
      ],
      showSymbolLogo: true,
      isTransparent: true,
      displayMode: "adaptive",
      colorTheme: "dark",
      locale: "en",
    });

    containerRef.current.innerHTML = "";
    const widgetDiv = document.createElement("div");
    widgetDiv.className = "tradingview-widget-container__widget";
    containerRef.current.appendChild(widgetDiv);
    containerRef.current.appendChild(script);

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }
    };
  }, []);

  return (
    <div className="border-b border-border bg-bg-card/50">
      <div
        ref={containerRef}
        className="tradingview-widget-container"
        style={{ height: "46px", overflow: "hidden" }}
      />
    </div>
  );
}

export default memo(MarketTickerInner);
