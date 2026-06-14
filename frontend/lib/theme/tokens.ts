/**
 * Design tokens — single source of truth for color, typography, and chart
 * theming. Mirrors CLAUDE.md ("Design System — Non-Negotiable Rules").
 *
 * tailwind.config.ts derives theme.colors and theme.fontSize from this file.
 * Chart.js / canvas / SVG code that cannot read Tailwind classes should
 * import `colors` or `chartTheme` directly instead of hardcoding hex values.
 */

export const colors = {
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
    low: "#1C3558",
    strong: "#1A6B3C",
  },
  tint: {
    severe: "#F5DADA",
    high: "#FAE8E8",
    moderate: "#FDF2DC",
    low: "#E4F2EB",
    strong: "#D6EDE0",
  },
  skeleton: "#E8E5DF",
};

export const fonts = {
  sans: "var(--font-sans)",
  serif: "var(--font-serif)",
  mono: "var(--font-mono)",
};

/**
 * Documented type scale. Per CLAUDE.md: body text 14-16px, all-caps section
 * labels 10-11px (letter-spacing 0.07em), UI headings via Inter 500-600,
 * hero headings via Playfair 400. These are named tokens for new code —
 * existing inline px values elsewhere are not retroactively migrated.
 */
export const typeScale = {
  "2xs": "10px", // all-caps section labels, table headers
  xs: "11px", // badges, tooltips, secondary labels
  sm: "12px", // captions, helper/error text, table meta
  base: "14px", // body text, inputs, nav, table cells
  md: "16px", // emphasized body / sub-headings
  lg: "18px", // card and dialog titles
  xl: "22px", // page titles
  "2xl": "28px", // section headers
  display: "36px", // rare hero numerals
  gauge: "52px", // integrity gauge digits — mobile
  "gauge-lg": "72px", // integrity gauge digits — desktop
};

/**
 * Chart.js-ready theme. Charts (Phase 6+) cannot read Tailwind utility
 * classes; import this object directly into Chart.js `options` / `data`.
 */
export const chartTheme = {
  fontFamily: fonts.sans,
  numericFontFamily: fonts.mono,
  labelFontSize: 11,
  numericFontSize: 12,
  gridColor: colors.border,
  axisColor: colors.text.secondary,
  tickColor: colors.text.muted,
  series: [
    colors.navy,
    colors.risk.moderate,
    colors.risk.high,
    colors.risk.strong,
    colors.text.muted,
  ],
  riskColors: colors.risk,
  tintColors: colors.tint,
};
