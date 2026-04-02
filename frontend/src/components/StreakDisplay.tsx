interface Props {
  data: {
    current_streak?: { type: string; count: number };
    max_win_streak?: number;
    max_loss_streak?: number;
    avg_win_streak?: number;
    avg_loss_streak?: number;
    streaks_history?: { type: string; count: number; pnl: number; start_date: string }[];
  };
}

export default function StreakDisplay({ data }: Props) {
  if (!data || !data.current_streak) return null;

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Streaks</h3>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        <div>
          <div className="text-xs text-gray-500 mb-1">Current Streak</div>
          <div
            className={`text-xl font-bold font-mono ${
              data.current_streak.type === "win" ? "text-win" : "text-loss"
            }`}
          >
            {data.current_streak.count} {data.current_streak.type === "win" ? "W" : "L"}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Max Win Streak</div>
          <div className="text-xl font-bold font-mono text-win">{data.max_win_streak}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Max Loss Streak</div>
          <div className="text-xl font-bold font-mono text-loss">{data.max_loss_streak}</div>
        </div>
      </div>

      {data.streaks_history && data.streaks_history.length > 0 && (
        <div>
          <div className="text-xs text-gray-500 uppercase mb-2">Recent Streaks</div>
          <div className="flex flex-wrap gap-1.5">
            {data.streaks_history.slice(-15).map((streak, i) => (
              <div
                key={i}
                className={`px-2 py-1 rounded text-xs font-mono font-medium ${
                  streak.type === "win"
                    ? "bg-win/15 text-win"
                    : "bg-loss/15 text-loss"
                }`}
                title={`${streak.count} ${streak.type}s, P&L: $${streak.pnl}`}
              >
                {streak.count}{streak.type === "win" ? "W" : "L"}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
