export interface OverviewMetrics {
  total_trades: number;
  winners: number;
  losers: number;
  scratches: number;
  win_rate: number;
  gross_profit: number;
  gross_loss: number;
  average_winner: number;
  average_loser: number;
  largest_winner: number;
  largest_loser: number;
  profit_factor: number | null;
  expectancy: number;
  total_pnl: number;
  total_fees: number;
  net_pnl: number;
  average_hold_time_minutes: number | null;
  best_day: { date: string; pnl: number };
  worst_day: { date: string; pnl: number };
}

export interface TimeAnalysis {
  win_rate_by_hour: Record<string, number>;
  pnl_by_hour: Record<string, number>;
  trades_by_hour: Record<string, number>;
  win_rate_by_day_of_week: Record<string, number>;
  pnl_by_day_of_week: Record<string, number>;
  trades_by_day_of_week: Record<string, number>;
  best_hour: number | null;
  worst_hour: number | null;
  best_day: string | null;
  worst_day: string | null;
  win_rate_by_session: Record<string, number>;
  pnl_by_session: Record<string, number>;
  trades_by_session: Record<string, number>;
}

export interface BehavioralData {
  insufficient_data?: boolean;
  revenge_trades?: {
    alert?: string | null;
    count?: number;
    win_rate?: number | null;
    total_pnl?: number | null;
    percentage_of_trades?: number;
    normal_win_rate?: number;
  };
  overtrading_days?: {
    alert?: string | null;
    count?: number;
    total_pnl_on_overtrading_days?: number;
  };
  tilt_detection?: {
    alert?: string | null;
    tilt_events?: number;
    total_pnl_from_tilt?: number;
  };
  win_streak_behavior?: {
    occurrences?: number;
    next_trade_win_rate?: number | null;
    next_trade_avg_pnl?: number | null;
    streak_threshold?: number;
  };
  loss_streak_behavior?: {
    occurrences?: number;
    next_trade_win_rate?: number | null;
    next_trade_avg_pnl?: number | null;
    streak_threshold?: number;
  };
  monday_effect?: {
    alert?: string | null;
    is_significant?: boolean;
    has_data?: boolean;
  };
  friday_effect?: {
    alert?: string | null;
    is_significant?: boolean;
    has_data?: boolean;
  };
  first_trade_of_day?: {
    alert?: string | null;
    has_data?: boolean;
  };
  last_trade_of_day?: {
    alert?: string | null;
    has_data?: boolean;
  };
  sizing_after_loss?: {
    alert?: string | null;
    has_data?: boolean;
  };
  time_between_trades?: {
    alert?: string | null;
    has_data?: boolean;
  };
}

export interface SymbolData {
  trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
  avg_hold_time: number | null;
}

export interface SymbolsAnalysis {
  per_symbol: Record<string, SymbolData>;
  best_symbols: Array<SymbolData & { symbol: string }>;
  worst_symbols: Array<SymbolData & { symbol: string }>;
  concentration_top3: number;
}

export interface Streak {
  type: string;
  count: number;
  pnl: number;
  start_date: string;
  end_date?: string;
}

export interface StreakAnalysis {
  current_streak: { type: string; count: number };
  max_win_streak: number;
  max_loss_streak: number;
  avg_win_streak: number;
  avg_loss_streak: number;
  streaks_history: Streak[];
}

export interface EquityCurvePoint {
  date: string;
  cumulative_pnl: number;
  trade_count: number;
}

export interface EquityCurveData {
  cumulative_pnl: EquityCurvePoint[];
  drawdown_periods: Array<{ start: string; end: string; depth: number }>;
  max_drawdown: { amount: number; start: string | null; end: string | null };
  rolling_win_rate_20: number[];
  rolling_pnl_20: number[];
}

export interface RiskMetrics {
  average_risk_reward: number | null;
  max_consecutive_losses: number;
  average_daily_pnl: number;
  std_daily_pnl: number;
  trading_days: number;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  var_95: number | null;
  calmar_ratio: number | null;
}

export interface Analytics {
  overview: OverviewMetrics;
  time_analysis: TimeAnalysis;
  behavioral: BehavioralData;
  symbols: SymbolsAnalysis;
  streaks: StreakAnalysis;
  equity_curve: EquityCurveData;
  risk_metrics: RiskMetrics;
}

export interface Trade {
  id: string;
  timestamp: string;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  duration_minutes: number | null;
  setup_type: string | null;
  notes: string | null;
  fees: number;
  mood: string | null;
  reason: string | null;
  rule_followed: boolean | null;
  mistake_category: string | null;
}

export interface IntelligenceAlert {
  id: string;
  type: string;
  severity: "critical" | "warning" | "info" | "positive";
  title: string;
  message: string;
  dollar_impact: number | null;
  affected_trades: number;
  recommendation: string | null;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  plan: string;
  timezone_offset: number;
}
