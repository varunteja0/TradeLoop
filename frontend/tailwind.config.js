/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0a0a0f",
          card: "#12121a",
          hover: "#1a1a28",
          input: "#0e0e16",
        },
        accent: "#00d4aa",
        loss: "#ff4757",
        win: "#00d4aa",
        muted: "#6b7280",
        border: "#1e1e2e",
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', "monospace"],
      },
    },
  },
  plugins: [],
};
