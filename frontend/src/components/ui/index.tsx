import { forwardRef, ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, HTMLAttributes } from "react";

// ============ BUTTON ============
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading, children, className = "", disabled, ...props }, ref) => {
    const variants = {
      primary: "bg-accent text-bg-primary font-semibold hover:brightness-110",
      secondary: "border border-border text-gray-300 font-medium hover:bg-bg-hover",
      danger: "border border-loss/30 text-loss font-medium hover:bg-loss/10",
      ghost: "text-gray-400 hover:text-white hover:bg-bg-hover",
    };
    const sizes = {
      sm: "px-3 py-1.5 text-xs",
      md: "px-5 py-2.5 text-sm",
      lg: "px-8 py-3.5 text-base",
    };
    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center gap-2 rounded-lg transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";

// ============ INPUT ============
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, className = "", ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div>
        {label && <label htmlFor={inputId} className="block text-sm text-gray-400 mb-1.5">{label}</label>}
        <input
          ref={ref}
          id={inputId}
          className={`w-full bg-bg-input border rounded-lg px-4 py-3 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent transition-colors duration-200 ${error ? "border-loss" : "border-border"} ${className}`}
          {...props}
        />
        {error && <p className="text-xs text-loss mt-1" role="alert">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";

// ============ CARD ============
interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  accent?: boolean;
  padding?: "sm" | "md" | "lg";
}

export function Card({ hover, accent, padding = "md", className = "", children, ...props }: CardProps) {
  const paddings = { sm: "p-3", md: "p-5", lg: "p-8" };
  return (
    <div
      className={`bg-bg-card border rounded-xl ${paddings[padding]} ${accent ? "border-accent/20" : "border-border"} ${hover ? "hover:border-accent/30 transition-colors duration-300" : ""} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

// ============ BADGE ============
interface BadgeProps {
  variant?: "success" | "warning" | "danger" | "info" | "neutral";
  children: ReactNode;
}

export function Badge({ variant = "neutral", children }: BadgeProps) {
  const styles = {
    success: "bg-win/20 text-win",
    warning: "bg-yellow-500/20 text-yellow-400",
    danger: "bg-loss/20 text-loss",
    info: "bg-accent/20 text-accent",
    neutral: "bg-gray-500/20 text-gray-400",
  };
  return <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${styles[variant]}`}>{children}</span>;
}

// ============ SKELETON ============
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse bg-bg-hover rounded ${className}`} />;
}

// ============ STAT ============
interface StatProps {
  label: string;
  value: string | number;
  change?: number;
  prefix?: string;
}

export function Stat({ label, value, change, prefix }: StatProps) {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-xl font-bold font-mono text-white">
        {prefix}{value}
      </p>
      {change !== undefined && change !== 0 && (
        <p className={`text-xs font-mono mt-1 ${change > 0 ? "text-win" : "text-loss"}`}>
          {change > 0 ? "▲" : "▼"} {Math.abs(change).toFixed(1)}
        </p>
      )}
    </div>
  );
}

// ============ EMPTY STATE ============
interface EmptyProps {
  icon?: string;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ icon = "📊", title, description, action }: EmptyProps) {
  return (
    <div className="text-center py-20">
      <div className="text-5xl mb-4 opacity-30">{icon}</div>
      <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
      <p className="text-gray-400 mb-6">{description}</p>
      {action}
    </div>
  );
}
