interface SymbolData {
  trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
  avg_hold_time: number | null;
}

interface Props {
  perSymbol: Record<string, SymbolData>;
}

export default function SymbolTable({ perSymbol }: Props) {
  const sorted = Object.entries(perSymbol).sort(
    ([, a], [, b]) => b.total_pnl - a.total_pnl
  );

  return (
    <div className="card overflow-x-auto">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Performance by Symbol</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-gray-500 uppercase border-b border-border">
            <th className="text-left pb-3 pr-4">Symbol</th>
            <th className="text-right pb-3 px-3">Trades</th>
            <th className="text-right pb-3 px-3">Win Rate</th>
            <th className="text-right pb-3 px-3">Total P&L</th>
            <th className="text-right pb-3 px-3">Avg P&L</th>
            <th className="text-right pb-3 pl-3 hidden sm:table-cell">Avg Hold</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(([symbol, data]) => (
            <tr key={symbol} className="border-b border-border/50 hover:bg-bg-hover transition-colors">
              <td className="py-3 pr-4 font-mono font-medium text-white">{symbol}</td>
              <td className="py-3 px-3 text-right text-gray-400">{data.trades}</td>
              <td className="py-3 px-3 text-right">
                <span className={data.win_rate >= 50 ? "text-win" : "text-loss"}>
                  {data.win_rate}%
                </span>
              </td>
              <td className="py-3 px-3 text-right">
                <span className={`font-mono ${data.total_pnl >= 0 ? "text-win" : "text-loss"}`}>
                  ${data.total_pnl.toFixed(2)}
                </span>
              </td>
              <td className="py-3 px-3 text-right">
                <span className={`font-mono ${data.avg_pnl >= 0 ? "text-win" : "text-loss"}`}>
                  ${data.avg_pnl.toFixed(2)}
                </span>
              </td>
              <td className="py-3 pl-3 text-right text-gray-400 hidden sm:table-cell">
                {data.avg_hold_time ? `${data.avg_hold_time.toFixed(0)}m` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
