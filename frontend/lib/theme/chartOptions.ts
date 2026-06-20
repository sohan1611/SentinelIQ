import type { ChartOptions, TooltipItem } from "chart.js"
import { chartTheme, colors } from "./tokens"

/**
 * Bloomberg/FT signature: label each line's current (last) value directly on
 * the chart, so the latest reading is readable at a glance without hovering.
 * A plain Chart.js plugin object (not a new dependency) -- pass via the
 * <Line>/<Bar> component's `plugins` prop, not `options`.
 */
export function createEndLabelPlugin(formatter: (value: number) => string) {
  return {
    id: "endLabel",
    afterDatasetsDraw(chart: any) {
      const { ctx, chartArea } = chart
      chart.data.datasets.forEach((dataset: any, i: number) => {
        const meta = chart.getDatasetMeta(i)
        if (meta.hidden) return
        const data = dataset.data as Array<number | null>
        let lastIndex = data.length - 1
        while (lastIndex >= 0 && data[lastIndex] == null) lastIndex--
        const point = meta.data[lastIndex]
        const value = data[lastIndex]
        if (!point || value == null) return

        const text = formatter(value)
        ctx.save()
        ctx.font = `600 ${chartTheme.numericFontSize}px ${chartTheme.numericFontFamily}`
        ctx.textBaseline = "middle"
        ctx.textAlign = "left"
        const textWidth = ctx.measureText(text).width
        const x = Math.min(point.x + 6, chartArea.right - textWidth)

        // Solid backing (not a shadow) so the label stays legible if it lands
        // on a gridline -- a real value, like this AAPL run's "50", can
        // coincide exactly with a Y-axis tick.
        ctx.fillStyle = colors.surface
        ctx.fillRect(x - 2, point.y - chartTheme.numericFontSize / 2 - 2, textWidth + 4, chartTheme.numericFontSize + 4)

        ctx.fillStyle = dataset.borderColor as string
        ctx.fillText(text, x, point.y)
        ctx.restore()
      })
    },
  }
}

// Shared Chart.js styling so every forensic chart matches the muted FT spec:
// hairline grid, mono tick labels, restrained tooltip — no per-component duplication.
export function baseChartOptions<TType extends "line" | "bar">(
  yTickFormatter: (value: number) => string,
  tooltipLabel?: (ctx: TooltipItem<TType>) => string,
  opts?: { emphasizeZero?: boolean }
): ChartOptions<TType> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index" as const, intersect: false },
    // Reserve room on the right for the end-of-line value label (createEndLabelPlugin).
    // Harmless on charts that don't use the plugin (e.g. the CashFlowChart bar chart).
    layout: { padding: { right: 36 } },
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
        // emphasizeZero: for charts where the metric can legitimately go
        // negative (a divergence, a growth rate), a bolder zero line makes
        // "above vs. below baseline" readable at a glance -- a deliberate
        // per-chart opt-in, not every chart's zero is a meaningful baseline
        // (e.g. a 0-100 score has no "crossing zero" semantic).
        grid: opts?.emphasizeZero
          ? {
              color: (ctx: any) => (ctx.tick?.value === 0 ? chartTheme.axisColor : chartTheme.gridColor),
              lineWidth: (ctx: any) => (ctx.tick?.value === 0 ? 1.5 : 1),
            }
          : { color: chartTheme.gridColor },
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
