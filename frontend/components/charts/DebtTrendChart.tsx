"use client"

import * as React from "react"
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from "chart.js"
import { Line } from "react-chartjs-2"
import { ChartFrame } from "@/components/ui/ChartFrame"
import { colors } from "@/lib/theme/tokens"
import { baseChartOptions, createEndLabelPlugin } from "@/lib/theme/chartOptions"
import { alignByPeriod } from "@/lib/utils/chartData"
import { formatPercent } from "@/lib/utils/formatNumber"
import type { DebtMetricPoint } from "@/types/analysis"

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend)

export interface DebtTrendChartProps {
  debtMetrics: DebtMetricPoint[];
  actions?: React.ReactNode;
}

export function DebtTrendChart({ debtMetrics, actions }: DebtTrendChartProps) {
  if (debtMetrics.length === 0) {
    return (
      <ChartFrame
        title="Debt Stress"
        subtitle="Debt-to-revenue and year-over-year debt growth"
        actions={actions}
      >
        <div className="flex items-center justify-center h-full font-sans text-sm text-text-muted text-center px-6">
          Not enough financial history to compute debt trends.
        </div>
      </ChartFrame>
    )
  }

  const { labels, data } = alignByPeriod([
    debtMetrics.map((d) => ({ period: d.period, value: d.debt_to_revenue })),
    debtMetrics.map((d) => ({ period: d.period, value: d.debt_growth })),
  ])

  const chartData = {
    labels,
    datasets: [
      {
        label: "Debt / Revenue",
        data: data[0],
        borderColor: colors.navy,
        backgroundColor: colors.navy,
        tension: 0,
        spanGaps: true,
      },
      {
        label: "Debt Growth (YoY)",
        data: data[1],
        borderColor: colors.risk.high,
        backgroundColor: colors.risk.high,
        tension: 0,
        spanGaps: true,
      },
    ],
  }

  const formatValue = (v: number) => formatPercent(v, 0)
  const options = baseChartOptions<"line">(
    formatValue,
    (ctx) => `${ctx.dataset.label}: ${formatPercent(ctx.parsed.y, 1)}`,
    { emphasizeZero: true }
  )

  return (
    <ChartFrame
      title="Debt Stress"
      subtitle="Debt-to-revenue and year-over-year debt growth"
      actions={actions}
      accessibleTable={{
        labels: chartData.labels,
        series: chartData.datasets.map((d) => ({ label: d.label, values: d.data, formatValue })),
      }}
    >
      <Line data={chartData} options={options} plugins={[createEndLabelPlugin(formatValue)]} />
    </ChartFrame>
  )
}
