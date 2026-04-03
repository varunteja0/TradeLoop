import React, { useMemo, useState, useCallback } from "react";
import type { SymbolData } from "../types";

interface Props {
  perSymbol: Record<string, SymbolData>;
}

type SortKey = "trades" | "win_rate" | "total_pnl" | "avg_pnl";
type SortDir = "asc" | "desc";

const columns: { key: SortKey; label: string; className: string }[] = [
  { key: "trades", label: "Trades", className: "text-right pb-3 px-3" },
  { key: "win_rate", label: "Win Rate", className: "text-right pb-3 px-3" },
  { key: "total_pnl", label: "Total P&L", className: "text-right pb-3 px-3" },
  { key: "avg_pnl", label: "Avg P&L", className: "text-right pb-3 px-3" },
];

const pnlIndicator = (v: number) => (v >= 0 ? "▲" : "▼");
const pnlPrefix = (v: number) => (v >= 0 ? "+" : "");

const SymbolTable = React.memo(function SymbolTable({ perSymbol }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("total_pnl");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSort = useCallback(
    (key: SortKey) => {
      if (key === sortKey) {
        setSortDir((d) => (d === "desc" ? "asc" : "desc"));
      } else {
        setSortKey(key);
        setSortDir("desc");
      }
    },
    [sortKey],
  );

  const sorted = useMemo(() => {
    const entries = Object.entries(perSymbol);
    return entries.sort(([, a], [, b]) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      return sortDir === "desc" ? bv - av : av - bv;
    });
  }, [perSymbol, sortKey, sortDir]);

  const ariaSortValue = (key: SortKey): "ascending" | "descending" | "none" => {
    if (key !== sortKey) return "none";
    return sortDir === "asc" ? "ascending" : "descending";
  };

  return (
    <div className="card overflow-x-auto">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">
        Performance by Symbol
      </h3>
      <table className="w-full text-sm" role="table">
        <thead>
          <tr className="text-xs text-gray-500 uppercase border-b border-border">
            <th className="text-left pb-3 pr-4" scope="col">Symbol</th>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`${col.className} cursor-pointer select-none hover:text-gray-300 transition-colors`}
                scope="col"
                aria-sort={ariaSortValue(col.key)}
                onClick={() => handleSort(col.key)}
              >
                {col.label}
                {sortKey === col.key && (
                  <span className="ml-1" aria-hidden="true">
                    {sortDir === "desc" ? "▼" : "▲"}
                  </span>
                )}
              </th>
            ))}
            <th className="text-right pb-3 pl-3 hidden sm:table-cell" scope="col">
              Avg Hold
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(([symbol, data]) => (
            <tr
              key={symbol}
              className="border-b border-border/50 hover:bg-bg-hover transition-colors"
            >
              <td className="py-3 pr-4 font-mono font-medium text-white">
                {symbol}
              </td>
              <td className="py-3 px-3 text-right text-gray-400">
                {data.trades}
              </td>
              <td className="py-3 px-3 text-right">
                <span
                  className={data.win_rate >= 50 ? "text-win" : "text-loss"}
                >
                  {data.win_rate}%
                </span>
              </td>
              <td className="py-3 px-3 text-right">
                <span
                  className={`font-mono ${data.total_pnl >= 0 ? "text-win" : "text-loss"}`}
                >
                  {pnlPrefix(data.total_pnl)}${data.total_pnl.toFixed(2)}
                  <span className="ml-1 text-xs" aria-hidden="true">
                    {pnlIndicator(data.total_pnl)}
                  </span>
                </span>
              </td>
              <td className="py-3 px-3 text-right">
                <span
                  className={`font-mono ${data.avg_pnl >= 0 ? "text-win" : "text-loss"}`}
                >
                  {pnlPrefix(data.avg_pnl)}${data.avg_pnl.toFixed(2)}
                  <span className="ml-1 text-xs" aria-hidden="true">
                    {pnlIndicator(data.avg_pnl)}
                  </span>
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
});

export default SymbolTable;
