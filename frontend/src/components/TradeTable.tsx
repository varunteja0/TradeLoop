import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import type { Trade } from "../types";

type SortKey = "timestamp" | "symbol" | "pnl" | "quantity";
type SortDir = "asc" | "desc";
type SideFilter = "ALL" | "BUY" | "SELL";

const sortableColumns: { key: SortKey; label: string; apiKey: string }[] = [
  { key: "timestamp", label: "Date", apiKey: "timestamp" },
  { key: "symbol", label: "Symbol", apiKey: "symbol" },
  { key: "quantity", label: "Qty", apiKey: "quantity" },
  { key: "pnl", label: "P&L", apiKey: "pnl" },
];

function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => {
    timerRef.current = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timerRef.current);
  }, [value, delay]);
  return debounced;
}

export default function TradeTable() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebouncedValue(searchInput, 300);
  const [sortKey, setSortKey] = useState<SortKey>("timestamp");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [sideFilter, setSideFilter] = useState<SideFilter>("ALL");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const perPage = 20;

  const fetchTrades = useCallback(() => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(perPage),
      sort_by: sortKey,
      sort_dir: sortDir,
    });
    if (search.trim()) params.set("search", search.trim());
    if (sideFilter !== "ALL") params.set("side", sideFilter);

    api
      .get(`/trades?${params.toString()}`)
      .then(({ data }) => {
        setTrades(data.trades);
        setTotal(data.total);
      })
      .catch((err) => {
        setError(
          err?.response?.data?.detail || "Failed to load trades. Please try again.",
        );
        setTrades([]);
        setTotal(0);
      })
      .finally(() => setLoading(false));
  }, [page, perPage, search, sortKey, sortDir, sideFilter]);

  useEffect(() => {
    fetchTrades();
  }, [fetchTrades]);

  useEffect(() => {
    setPage(1);
  }, [search, sideFilter, sortKey, sortDir]);

  const totalPages = useMemo(
    () => Math.ceil(total / perPage),
    [total, perPage],
  );

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

  const handleDelete = useCallback(
    (id: string) => {
      if (!window.confirm("Delete this trade? This action cannot be undone."))
        return;
      setDeletingId(id);
      api
        .delete(`/trades/${id}`)
        .then(() => fetchTrades())
        .catch((err) => {
          setError(
            err?.response?.data?.detail || "Failed to delete trade.",
          );
        })
        .finally(() => setDeletingId(null));
    },
    [fetchTrades],
  );

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editingReason, setEditingReason] = useState<string>("");

  const handleFieldChange = useCallback(
    (tradeId: string, field: string, value: unknown) => {
      setTrades((prev) =>
        prev.map((t) =>
          t.id === tradeId ? { ...t, [field]: value || null } : t,
        ),
      );
      api.patch(`/trades/${tradeId}`, { [field]: value || null }).catch(() => {
        fetchTrades();
      });
    },
    [fetchTrades],
  );

  const ariaSortValue = (
    key: SortKey,
  ): "ascending" | "descending" | "none" => {
    if (key !== sortKey) return "none";
    return sortDir === "asc" ? "ascending" : "descending";
  };

  return (
    <div className="card overflow-x-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <h3 className="text-sm font-semibold text-gray-300">
          Trade History
          <span className="ml-2 text-gray-500 font-normal">
            ({total} total)
          </span>
        </h3>

        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search symbol…"
            aria-label="Search trades by symbol"
            className="px-3 py-1.5 text-sm rounded-lg bg-bg-hover border border-border text-white placeholder-gray-500 focus:outline-none focus:border-accent w-40"
          />

          <div className="flex rounded-lg border border-border overflow-hidden" role="group" aria-label="Filter by side">
            {(["ALL", "BUY", "SELL"] as SideFilter[]).map((side) => (
              <button
                key={side}
                onClick={() => setSideFilter(side)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  sideFilter === side
                    ? "bg-accent/20 text-accent"
                    : "text-gray-400 hover:text-white"
                }`}
                aria-pressed={sideFilter === side}
              >
                {side}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div
          className="mb-4 p-3 rounded-lg border border-loss/40 bg-loss/5 text-sm text-loss"
          role="alert"
        >
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading…</div>
      ) : trades.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {search || sideFilter !== "ALL"
            ? "No trades match your filters."
            : "No trades yet. Upload a CSV to get started."}
        </div>
      ) : (
        <>
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="text-xs text-gray-500 uppercase border-b border-border">
                {sortableColumns.map((col) => {
                  if (col.key === "timestamp") {
                    return (
                      <th
                        key={col.key}
                        className="text-left pb-3 pr-2 cursor-pointer select-none hover:text-gray-300 transition-colors"
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
                    );
                  }
                  if (col.key === "symbol") {
                    return (
                      <th
                        key={col.key}
                        className="text-left pb-3 px-2 cursor-pointer select-none hover:text-gray-300 transition-colors"
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
                    );
                  }
                  return null;
                })}
                <th className="text-left pb-3 px-2" scope="col">Side</th>
                <th className="text-right pb-3 px-2" scope="col">Entry</th>
                <th className="text-right pb-3 px-2" scope="col">Exit</th>
                {sortableColumns.map((col) => {
                  if (col.key === "quantity") {
                    return (
                      <th
                        key={col.key}
                        className="text-right pb-3 px-2 cursor-pointer select-none hover:text-gray-300 transition-colors"
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
                    );
                  }
                  if (col.key === "pnl") {
                    return (
                      <th
                        key={col.key}
                        className="text-right pb-3 px-2 cursor-pointer select-none hover:text-gray-300 transition-colors"
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
                    );
                  }
                  return null;
                })}
                <th className="text-left pb-3 pl-2 hidden md:table-cell" scope="col">
                  Setup
                </th>
                <th className="text-left pb-3 px-2 hidden md:table-cell" scope="col">
                  Mood
                </th>
                <th className="text-left pb-3 px-2 hidden lg:table-cell" scope="col">
                  Mistake
                </th>
                <th className="text-center pb-3 px-2 hidden lg:table-cell" scope="col">
                  Rule
                </th>
                <th className="text-right pb-3 px-2" scope="col">
                  Replay
                </th>
                <th className="pb-3 pl-2 w-10" scope="col">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <React.Fragment key={t.id}>
                <tr
                  className="border-b border-border/30 hover:bg-bg-hover transition-colors"
                >
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
                  <td className="py-2 px-2 font-mono font-medium text-white text-xs">
                    {t.symbol}
                  </td>
                  <td className="py-2 px-2">
                    <span
                      className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                        t.side === "BUY"
                          ? "bg-win/15 text-win"
                          : "bg-loss/15 text-loss"
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
                  <td className="py-2 px-2 text-right font-mono text-xs text-gray-400">
                    {t.quantity}
                  </td>
                  <td
                    className={`py-2 px-2 text-right font-mono text-xs font-medium ${
                      t.pnl >= 0 ? "text-win" : "text-loss"
                    }`}
                  >
                    {t.pnl >= 0 ? "+" : ""}₹{Math.abs(t.pnl).toFixed(2)}
                    <span className="ml-0.5" aria-hidden="true">
                      {t.pnl >= 0 ? "▲" : "▼"}
                    </span>
                  </td>
                  <td className="py-2 pl-2 text-xs text-gray-500 hidden md:table-cell">
                    {t.setup_type || "—"}
                  </td>
                  <td className="py-2 px-2 hidden md:table-cell">
                    <select
                      value={t.mood || ""}
                      onChange={(e) =>
                        handleFieldChange(t.id, "mood", e.target.value)
                      }
                      className="bg-transparent text-xs text-gray-400 border-0 focus:ring-0 cursor-pointer"
                    >
                      <option value="">—</option>
                      <option value="confident">😎 Confident</option>
                      <option value="calm">😌 Calm</option>
                      <option value="fearful">😰 Fearful</option>
                      <option value="anxious">😟 Anxious</option>
                      <option value="fomo">🔥 FOMO</option>
                      <option value="revenge">😤 Revenge</option>
                      <option value="greedy">🤑 Greedy</option>
                      <option value="bored">😑 Bored</option>
                      <option value="neutral">😐 Neutral</option>
                    </select>
                  </td>
                  <td className="py-2 px-2 hidden lg:table-cell">
                    <select
                      value={t.mistake_category || ""}
                      onChange={(e) =>
                        handleFieldChange(t.id, "mistake_category", e.target.value)
                      }
                      className="bg-transparent text-xs text-gray-400 border-0 focus:ring-0 cursor-pointer"
                    >
                      <option value="">—</option>
                      <option value="none">None</option>
                      <option value="fomo_entry">FOMO Entry</option>
                      <option value="revenge">Revenge</option>
                      <option value="early_exit">Early Exit</option>
                      <option value="late_exit">Late Exit</option>
                      <option value="no_stop_loss">No SL</option>
                      <option value="moved_stop_loss">Moved SL</option>
                      <option value="oversized">Oversized</option>
                      <option value="undersized">Undersized</option>
                      <option value="chased">Chased</option>
                      <option value="ignored_signal">Ignored Signal</option>
                      <option value="overtraded">Overtraded</option>
                    </select>
                  </td>
                  <td className="py-2 px-2 text-center hidden lg:table-cell">
                    <button
                      onClick={() =>
                        handleFieldChange(
                          t.id,
                          "rule_followed",
                          t.rule_followed === true ? false : t.rule_followed === false ? null : true,
                        )
                      }
                      className={`text-xs font-medium px-1.5 py-0.5 rounded transition-colors ${
                        t.rule_followed === true
                          ? "bg-win/15 text-win"
                          : t.rule_followed === false
                            ? "bg-loss/15 text-loss"
                            : "text-gray-600 hover:text-gray-400"
                      }`}
                      title={
                        t.rule_followed === true
                          ? "Rule followed — click to mark broken"
                          : t.rule_followed === false
                            ? "Rule broken — click to clear"
                            : "Click to mark rule followed"
                      }
                    >
                      {t.rule_followed === true ? "Yes" : t.rule_followed === false ? "No" : "—"}
                    </button>
                  </td>
                  <td className="py-2 px-2 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => {
                          if (expandedId === t.id) {
                            setExpandedId(null);
                          } else {
                            setExpandedId(t.id);
                            setEditingReason(t.reason || "");
                          }
                        }}
                        className="text-gray-600 hover:text-gray-300 transition-colors"
                        title="Trade details"
                      >
                        <svg className={`w-3.5 h-3.5 transition-transform ${expandedId === t.id ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      <Link
                        to={`/replay/${t.id}`}
                        className="text-accent hover:underline text-xs"
                      >
                        Replay
                      </Link>
                    </div>
                  </td>
                  <td className="py-2 pl-2">
                    <button
                      onClick={() => handleDelete(t.id)}
                      disabled={deletingId === t.id}
                      className="text-gray-600 hover:text-loss transition-colors disabled:opacity-30"
                      aria-label={`Delete trade ${t.symbol} on ${t.timestamp}`}
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth="2"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </td>
                </tr>
                {expandedId === t.id && (
                  <tr className="bg-bg-hover/50">
                    <td colSpan={12} className="px-4 py-3">
                      <div className="flex flex-col sm:flex-row gap-4">
                        <div className="flex-1">
                          <label className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-1 block">
                            Reason for Trade
                          </label>
                          <input
                            type="text"
                            value={editingReason}
                            onChange={(e) => setEditingReason(e.target.value)}
                            onBlur={() => {
                              if (editingReason !== (t.reason || "")) {
                                handleFieldChange(t.id, "reason", editingReason);
                              }
                            }}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleFieldChange(t.id, "reason", editingReason);
                                (e.target as HTMLInputElement).blur();
                              }
                            }}
                            placeholder="e.g. Break of structure on 15m, confluence with supply zone"
                            className="w-full px-3 py-1.5 text-sm rounded-lg bg-bg-primary border border-border text-white placeholder-gray-600 focus:outline-none focus:border-accent"
                          />
                        </div>
                        <div className="flex gap-4 sm:gap-6 text-xs">
                          <div>
                            <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold block mb-1">Duration</span>
                            <span className="text-gray-300">{t.duration_minutes ? `${Math.round(t.duration_minutes)}m` : "—"}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold block mb-1">Fees</span>
                            <span className="text-gray-300">{t.fees ? `₹${t.fees.toFixed(2)}` : "—"}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold block mb-1">Notes</span>
                            <span className="text-gray-400 max-w-[200px] truncate block">{t.notes || "—"}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
                </React.Fragment>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                aria-label="Go to previous page"
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
                aria-label="Go to next page"
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
