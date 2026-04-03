import React, { useMemo } from "react";
import type { TimeAnalysis } from "../types";

interface Props {
  winRateByHour: TimeAnalysis["win_rate_by_hour"];
  pnlByHour: TimeAnalysis["pnl_by_hour"];
  winRateByDay: TimeAnalysis["win_rate_by_day_of_week"];
  pnlByDay: TimeAnalysis["pnl_by_day_of_week"];
}

const getColor = (wr: number) => {
  if (wr >= 65) return "bg-win/30 text-win";
  if (wr >= 55) return "bg-win/15 text-win/80";
  if (wr >= 45) return "bg-gray-700/30 text-gray-400";
  if (wr >= 35) return "bg-loss/15 text-loss/80";
  return "bg-loss/30 text-loss";
};

const getTextIndicator = (wr: number) => {
  if (wr >= 55) return "+";
  if (wr <= 45) return "−";
  return "~";
};

const TimeHeatmap = React.memo(function TimeHeatmap({
  winRateByHour,
  pnlByHour,
  winRateByDay,
  pnlByDay,
}: Props) {
  const hours = useMemo(
    () =>
      Object.entries(winRateByHour).sort(
        ([a], [b]) => Number(a) - Number(b),
      ),
    [winRateByHour],
  );

  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

  return (
    <div className="card" role="region" aria-label="Performance by time heatmap">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">
        Performance by Time
      </h3>

      <div className="mb-6">
        <h4 className="text-xs text-gray-500 uppercase mb-3">By Hour</h4>
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
          {hours.map(([hour, wr]) => {
            const pnl = pnlByHour[hour] ?? 0;
            return (
              <div
                key={hour}
                className={`rounded-lg p-2 text-center ${getColor(wr)}`}
                aria-label={`Hour ${hour}: win rate ${wr}%, P&L $${pnl.toFixed(0)}`}
              >
                <div className="text-xs opacity-70">{hour}:00</div>
                <div className="text-sm font-bold">
                  <span aria-hidden="true">{getTextIndicator(wr)} </span>
                  {wr}%
                </div>
                <div className="text-[10px] opacity-60">
                  ${pnl.toFixed(0)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <h4 className="text-xs text-gray-500 uppercase mb-3">By Day</h4>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {days.map((day) => {
            const wr = winRateByDay[day];
            if (wr === undefined) return null;
            const pnl = pnlByDay[day] ?? 0;
            return (
              <div
                key={day}
                className={`rounded-lg p-3 text-center ${getColor(wr)}`}
                aria-label={`${day}: win rate ${wr}%, P&L $${pnl.toFixed(0)}`}
              >
                <div className="text-xs opacity-70">{day.slice(0, 3)}</div>
                <div className="text-lg font-bold">
                  <span aria-hidden="true">{getTextIndicator(wr)} </span>
                  {wr}%
                </div>
                <div className="text-xs opacity-60">
                  ${pnl.toFixed(0)}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
});

export default TimeHeatmap;
