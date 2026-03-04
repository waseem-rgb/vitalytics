import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        indigo: {
          DEFAULT: "#6366F1",
          hover: "#4F46E5",
          light: "#EEF2FF",
        },
        slate: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
          900: "#0F172A",
        },
        status: {
          critical: "#DC2626",
          "critical-bg": "#FEF2F2",
          high: "#EA580C",
          "high-bg": "#FFF7ED",
          abnormal: "#D97706",
          "abnormal-bg": "#FFFBEB",
          low: "#2563EB",
          "low-bg": "#EFF6FF",
          normal: "#059669",
          "normal-bg": "#ECFDF5",
        },
      },
      fontFamily: {
        sans: ['"Sora"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      borderRadius: {
        xl: "12px",
        "2xl": "14px",
        "3xl": "16px",
      },
    },
  },
  plugins: [],
};
export default config;
