import React, { useMemo } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import type { EquityCurvePoint } from "../types";

interface Props {
  data: EquityCurvePoint[] | undefined;
  loading?: boolean;
}

const EquityCurve = React.memo(function EquityCurve({ data, loading }: Props) {
  const summary = useMemo(() => {
    if (!data || data.length === 0) return null;
    const first = data[0];
    const last = data[data.length - 1];
    const direction = last.cumulative_pnl >= first.cumulative_pnl ? "up" : "down";
    return `Equity curve from ${first.date} to ${last.date}, trending ${direction}. Final cumulative P&L: ₹${last.cumulative_pnl.toFixed(2)} across ${last.trade_count} trades.`;
  }, [data]);

  if (loading) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Equity Curve</h3>
        <div className="h-72 flex items-center justify-center text-gray-500 text-sm">
          Loading equity curve…
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Equity Curve</h3>
        <div className="h-72 flex items-center justify-center text-gray-500 text-sm">
          No data available. Add trades to see your equity curve.
        </div>
      </div>
    );
  }

  return (
    <div className="card" role="figure" aria-label="Equity curve chart">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Equity Curve</h3>
      <span className="sr-only">{summary}</span>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
            <XAxis
              dataKey="date"
              tick={{ fill: "#6b7280", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "#1e1e2e" }}
              tickFormatter={(v: string) => v.slice(5)}
            />
            <YAxis
              tick={{ fill: "#6b7280", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "#1e1e2e" }}
              tickFormatter={(v: number) => `₹${v}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#12121a",
                border: "1px solid #1e1e2e",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: "#9ca3af" }}
              formatter={(value: number) => [
                `₹${value.toFixed(2)}`,
                "Cumulative P&L",
              ]}
            />
            <Area
              type="monotone"
              dataKey="cumulative_pnl"
              stroke="#00d4aa"
              strokeWidth={2}
              fill="url(#pnlGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

export default EquityCurve;
