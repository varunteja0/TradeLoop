import { Link } from "react-router-dom";
import { useAuth } from "../store/auth";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  linkTo?: string;
  className?: string;
}

const sizes = {
  sm: { box: "w-7 h-7 rounded-md", svg: 14, text: "text-lg" },
  md: { box: "w-8 h-8 rounded-lg", svg: 18, text: "text-xl" },
  lg: { box: "w-10 h-10 rounded-lg", svg: 22, text: "text-2xl" },
};

export default function Logo({ size = "md", showText = true, linkTo, className = "" }: LogoProps) {
  const user = useAuth((s) => s.user);
  const s = sizes[size];
  const href = linkTo ?? (user ? "/dashboard" : "/");

  const content = (
    <span className={`flex items-center gap-2 ${className}`}>
      <span className={`${s.box} bg-accent flex items-center justify-center`}>
        <svg width={s.svg} height={s.svg} viewBox="0 0 24 24" fill="none" stroke="#0a0a0f"
          strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" role="img" aria-label="TradeLoop logo">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      </span>
      {showText && <span className={`${s.text} font-bold text-white`}>TradeLoop</span>}
    </span>
  );

  return <Link to={href} aria-label="TradeLoop home">{content}</Link>;
}
