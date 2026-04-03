import React, { useMemo } from "react";
import type { BehavioralData } from "../types";

interface Props {
  data: BehavioralData;
}

type AlertType = "danger" | "warning" | "info";

interface Alert {
  type: AlertType;
  text: string;
}

const colors: Record<AlertType, string> = {
  danger: "border-loss/40 bg-loss/5",
  warning: "border-yellow-500/30 bg-yellow-500/5",
  info: "border-accent/30 bg-accent/5",
};

const iconColors: Record<AlertType, string> = {
  danger: "text-loss",
  warning: "text-yellow-400",
  info: "text-accent",
};

function AlertIcon({ type }: { type: AlertType }) {
  if (type === "danger") {
    return (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    );
  }
  if (type === "warning") {
    return (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  }
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

const BehaviorAlerts = React.memo(function BehaviorAlerts({ data }: Props) {
  const alerts = useMemo(() => {
    const result: Alert[] = [];

    const addAlert = (
      alert: string | null | undefined,
      type: AlertType = "warning",
    ) => {
      if (alert) result.push({ type, text: alert });
    };

    addAlert(data.revenge_trades?.alert, "danger");
    addAlert(data.overtrading_days?.alert, "danger");
    addAlert(data.tilt_detection?.alert, "danger");
    addAlert(data.friday_effect?.alert, "warning");
    addAlert(data.monday_effect?.alert, "info");
    addAlert(data.first_trade_of_day?.alert, "info");
    addAlert(data.last_trade_of_day?.alert, "warning");
    addAlert(data.sizing_after_loss?.alert, "warning");
    addAlert(data.time_between_trades?.alert, "info");

    if (
      data.win_streak_behavior?.occurrences &&
      data.win_streak_behavior.occurrences > 0
    ) {
      result.push({
        type: "info",
        text: `After 3+ win streaks (${data.win_streak_behavior.occurrences} times), your next trade wins ${data.win_streak_behavior.next_trade_win_rate}% of the time with avg P&L $${data.win_streak_behavior.next_trade_avg_pnl}.`,
      });
    }

    if (
      data.loss_streak_behavior?.occurrences &&
      data.loss_streak_behavior.occurrences > 0
    ) {
      result.push({
        type: "warning",
        text: `After 3+ loss streaks (${data.loss_streak_behavior.occurrences} times), your next trade wins ${data.loss_streak_behavior.next_trade_win_rate}% of the time with avg P&L $${data.loss_streak_behavior.next_trade_avg_pnl}.`,
      });
    }

    return result;
  }, [data]);

  if (data.insufficient_data) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">
          Behavioral Patterns
        </h3>
        <p className="text-gray-500 text-sm">
          Need at least 5 trades for behavioral analysis.
        </p>
      </div>
    );
  }

  const criticalCount = alerts.filter((a) => a.type === "danger").length;

  return (
    <div className="card" role="region" aria-label="Behavioral pattern alerts">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">
        Behavioral Patterns
        {criticalCount > 0 && (
          <span className="ml-2 px-2 py-0.5 bg-loss/20 text-loss text-xs rounded-full">
            {criticalCount} critical
          </span>
        )}
      </h3>

      {alerts.length === 0 ? (
        <p className="text-gray-500 text-sm">
          No significant behavioral patterns detected. Nice discipline!
        </p>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert, i) => (
            <div
              key={i}
              className={`border rounded-lg p-3 ${colors[alert.type]}`}
              {...(alert.type === "danger" ? { role: "alert" } : {})}
            >
              <div className="flex items-start gap-2">
                <span className={`mt-0.5 ${iconColors[alert.type]}`}>
                  <AlertIcon type={alert.type} />
                </span>
                <p className="text-sm text-gray-300">{alert.text}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

export default BehaviorAlerts;
