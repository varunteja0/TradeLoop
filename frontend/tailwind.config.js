/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#07070c",
          card: "#0d0d14",
          hover: "#12121f",
          input: "#0a0a12",
          sidebar: "#0a0a11",
        },
        accent: "#00d4aa",
        loss: "#ff4757",
        win: "#00d4aa",
        muted: "#6b7280",
        border: "#1a1a2e",
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"SF Mono"', 'monospace'],
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'glow': '0 0 30px rgba(0, 212, 170, 0.08)',
        'glow-strong': '0 0 60px rgba(0, 212, 170, 0.15)',
        'card': '0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3)',
        'elevated': '0 4px 24px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
};
