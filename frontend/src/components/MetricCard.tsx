interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  positive?: boolean | null;
}

export default function MetricCard({ label, value, subValue, positive }: MetricCardProps) {
  return (
    <div className="card">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</div>
      <div
        className={`text-2xl font-bold font-mono ${
          positive === true
            ? "text-win"
            : positive === false
            ? "text-loss"
            : "text-white"
        }`}
      >
        {value}
      </div>
      {subValue && <div className="text-xs text-gray-500 mt-1">{subValue}</div>}
    </div>
  );
}
