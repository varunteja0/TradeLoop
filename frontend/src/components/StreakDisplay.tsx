import React from "react";
import type { StreakAnalysis } from "../types";

interface Props {
  data: StreakAnalysis | undefined;
}

const StreakDisplay = React.memo(function StreakDisplay({ data }: Props) {
  if (!data || !data.current_streak) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Streaks</h3>
        <p className="text-gray-500 text-sm">
          No streak data available yet. Complete more trades to see streak
          analysis.
        </p>
      </div>
    );
  }

  const isWin = data.current_streak.type === "win";

  return (
    <div className="card" role="region" aria-label="Trading streaks summary">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Streaks</h3>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        <div>
          <div className="text-xs text-gray-500 mb-1">Current Streak</div>
          <div
            className={`text-xl font-bold font-mono ${isWin ? "text-win" : "text-loss"}`}
            aria-label={`Current streak: ${data.current_streak.count} ${isWin ? "wins" : "losses"}`}
          >
            {data.current_streak.count} {isWin ? "W" : "L"}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Max Win Streak</div>
          <div
            className="text-xl font-bold font-mono text-win"
            aria-label={`Maximum win streak: ${data.max_win_streak}`}
          >
            {data.max_win_streak}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Max Loss Streak</div>
          <div
            className="text-xl font-bold font-mono text-loss"
            aria-label={`Maximum loss streak: ${data.max_loss_streak}`}
          >
            {data.max_loss_streak}
          </div>
        </div>
      </div>

      {data.streaks_history && data.streaks_history.length > 0 && (
        <div>
          <div className="text-xs text-gray-500 uppercase mb-2">
            Recent Streaks
          </div>
          <div className="flex flex-wrap gap-1.5">
            {data.streaks_history.slice(-15).map((streak, i) => {
              const streakIsWin = streak.type === "win";
              return (
                <div
                  key={i}
                  className={`px-2 py-1 rounded text-xs font-mono font-medium ${
                    streakIsWin
                      ? "bg-win/15 text-win"
                      : "bg-loss/15 text-loss"
                  }`}
                  title={`${streak.count} ${streak.type}s, P&L: $${streak.pnl}`}
                  aria-label={`${streak.count} ${streak.type === "win" ? "win" : "loss"} streak, P&L $${streak.pnl.toFixed(2)}`}
                >
                  {streak.count}
                  {streakIsWin ? "W" : "L"}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
});

export default StreakDisplay;
