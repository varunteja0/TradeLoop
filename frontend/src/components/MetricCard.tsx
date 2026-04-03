import React from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  positive?: boolean | null;
}

export default React.memo(function MetricCard({ label, value, subValue, positive }: MetricCardProps) {
  return (
    <div className="card group hover:border-accent/20 transition-all duration-300">
      <div className="section-label mb-2">{label}</div>
      <div
        className={`stat-value ${
          positive === true
            ? "text-emerald-400"
            : positive === false
            ? "text-red-400"
            : "text-white"
        }`}
        aria-label={`${label}: ${value}`}
      >
        {value}
      </div>
      {subValue && <div className="text-[11px] text-gray-500 mt-1.5 font-mono">{subValue}</div>}
    </div>
  );
});
