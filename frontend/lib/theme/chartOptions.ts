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
        padding: 8,
        titleFont: { family: chartTheme.fontFamily, size: chartTheme.labelFontSize, weight: "bold" as const },
        bodyFont: { family: chartTheme.numericFontFamily, size: chartTheme.numericFontSize },
        callbacks: tooltipLabel ? { label: tooltipLabel } : undefined,
      },
    },
    scales: {
      x: {
        grid: { color: chartTheme.gridColor },
        ticks: { color: chartTheme.tickColor, font: { family: chartTheme.fontFamily, size: chartTheme.labelFontSize } },
        border: { color: chartTheme.gridColor },
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
