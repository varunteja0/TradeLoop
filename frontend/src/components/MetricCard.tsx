import React from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  positive?: boolean | null;
}

const MetricCard = React.memo(function MetricCard({
  label,
  value,
  subValue,
  positive,
}: MetricCardProps) {
  const indicator =
    positive === true ? " ▲" : positive === false ? " ▼" : "";

  const colorClass =
    positive === true
      ? "text-win"
      : positive === false
        ? "text-loss"
        : "text-white";

  const ariaDesc =
    positive === true
      ? `${label}: ${value}, positive`
      : positive === false
        ? `${label}: ${value}, negative`
        : `${label}: ${value}`;

  return (
    <div className="card" role="group" aria-label={ariaDesc}>
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={`text-2xl font-bold font-mono ${colorClass}`}>
        {value}
        {indicator && (
          <span className="text-base ml-1" aria-hidden="true">
            {indicator}
          </span>
        )}
      </div>
      {subValue && (
        <div className="text-xs text-gray-500 mt-1">{subValue}</div>
      )}
    </div>
  );
});

export default MetricCard;
