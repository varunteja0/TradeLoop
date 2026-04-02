interface Props {
  winRateByHour: Record<string, number>;
  pnlByHour: Record<string, number>;
  winRateByDay: Record<string, number>;
  pnlByDay: Record<string, number>;
}

export default function TimeHeatmap({ winRateByHour, pnlByHour, winRateByDay, pnlByDay }: Props) {
  const hours = Object.entries(winRateByHour).sort(([a], [b]) => Number(a) - Number(b));
  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

  const getColor = (wr: number) => {
    if (wr >= 65) return "bg-win/30 text-win";
    if (wr >= 55) return "bg-win/15 text-win/80";
    if (wr >= 45) return "bg-gray-700/30 text-gray-400";
    if (wr >= 35) return "bg-loss/15 text-loss/80";
    return "bg-loss/30 text-loss";
  };

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Performance by Time</h3>

      <div className="mb-6">
        <h4 className="text-xs text-gray-500 uppercase mb-3">By Hour</h4>
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
          {hours.map(([hour, wr]) => (
            <div
              key={hour}
              className={`rounded-lg p-2 text-center ${getColor(wr)}`}
            >
              <div className="text-xs opacity-70">{hour}:00</div>
              <div className="text-sm font-bold">{wr}%</div>
              <div className="text-[10px] opacity-60">
                ${pnlByHour[hour]?.toFixed(0) || 0}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h4 className="text-xs text-gray-500 uppercase mb-3">By Day</h4>
        <div className="grid grid-cols-5 gap-2">
          {days.map((day) => {
            const wr = winRateByDay[day];
            if (wr === undefined) return null;
            return (
              <div
                key={day}
                className={`rounded-lg p-3 text-center ${getColor(wr)}`}
              >
                <div className="text-xs opacity-70">{day.slice(0, 3)}</div>
                <div className="text-lg font-bold">{wr}%</div>
                <div className="text-xs opacity-60">
                  ${pnlByDay[day]?.toFixed(0) || 0}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
