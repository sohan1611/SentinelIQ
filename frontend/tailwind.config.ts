import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#F6F4EF",
        surface: "#FFFFFF",
        border: "#E3DFD8",
        navy: "#1C3558",
        text: {
          primary: "#1A1A18",
          secondary: "#7A786F",
          muted: "#B0ADA7",
        },
        risk: {
          severe: "#6E1010",
          high: "#B03028",
          moderate: "#C47A14",
          low: "#1A6B3C",
          strong: "#155E34",
        },
        tint: {
          severe: "#F5DADA",
          high: "#FAE8E8",
          moderate: "#FDF2DC",
          low: "#E4F2EB",
          strong: "#D6EDE0",
        },
        skeleton: "#E8E5DF",
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
