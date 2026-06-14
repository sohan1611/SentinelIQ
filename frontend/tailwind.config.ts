import type { Config } from "tailwindcss";
import { colors, typeScale } from "./lib/theme/tokens";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors,
      fontSize: {
        "2xs": typeScale["2xs"],
        md: typeScale.md,
        display: typeScale.display,
        gauge: typeScale.gauge,
        "gauge-lg": typeScale["gauge-lg"],
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        serif: ["var(--font-serif)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        card: "8px",
        btn: "6px",
      },
      transitionDuration: {
        instant: "var(--duration-instant)",
        fast: "var(--duration-fast)",
        base: "var(--duration-base)",
        slow: "var(--duration-slow)",
        deliberate: "var(--duration-deliberate)",
      },
      transitionTimingFunction: {
        out: "var(--ease-out)",
        in: "var(--ease-in)",
        base: "var(--ease-base)",
      },
    },
  },
  plugins: [],
};
export default config;
