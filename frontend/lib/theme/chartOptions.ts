import type { ChartOptions, TooltipItem } from "chart.js"
import { chartTheme, colors } from "./tokens"

// Shared Chart.js styling so every forensic chart matches the muted FT spec:
// hairline grid, mono tick labels, restrained tooltip — no per-component duplication.
export function baseChartOptions<TType extends "line" | "bar">(
  yTickFormatter: (value: number) => string,
  tooltipLabel?: (ctx: TooltipItem<TType>) => string
): ChartOptions<TType> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index" as const, intersect: false },
    // Restrained, FT/Bloomberg-style point markers: invisible at rest (the line
    // itself carries the data), a single clear dot appears under the cursor on
    // hover via the index-mode interaction above. Has no effect on bar charts.
    elements: {
      point: { radius: 0, hoverRadius: 5, hoverBorderWidth: 2 },
    },
    plugins: {
      legend: {
        position: "top" as const,
        align: "end" as const,
        labels: {
          usePointStyle: true,
          boxWidth: 8,
          boxHeight: 8,
          padding: 16,
          font: { family: chartTheme.fontFamily, size: chartTheme.labelFontSize },
          color: chartTheme.axisColor,
        },
      },
      tooltip: {
        backgroundColor: colors.surface,
        titleColor: colors.text.primary,
        bodyColor: colors.text.primary,
        borderColor: chartTheme.gridColor,
        borderWidth: 1,
        padding: 10,
        cornerRadius: 4,
        caretSize: 6,
        boxPadding: 4,
        bodySpacing: 6,
        usePointStyle: true,
        titleFont: { family: chartTheme.fontFamily, size: chartTheme.labelFontSize, weight: "bold" as const },
        bodyFont: { family: chartTheme.numericFontFamily, size: chartTheme.numericFontSize },
        callbacks: tooltipLabel ? { label: tooltipLabel } : undefined,
      },
    },
    scales: {
      x: {
        // No vertical gridlines and no boxed axis line -- FT/Bloomberg charts
        // read time left-to-right off the tick labels alone; only the Y-axis
        // carries reference lines.
        grid: { display: false },
        ticks: { color: chartTheme.tickColor, font: { family: chartTheme.fontFamily, size: chartTheme.labelFontSize } },
        border: { display: false },
      },
      y: {
        grid: { color: chartTheme.gridColor },
        ticks: {
          color: chartTheme.tickColor,
          font: { family: chartTheme.numericFontFamily, size: chartTheme.numericFontSize },
          callback: (value: string | number) => yTickFormatter(Number(value)),
        },
        border: { display: false },
      },
    },
  } as unknown as ChartOptions<TType>
}
