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
import { baseChartOptions } from "@/lib/theme/chartOptions"
import { alignByPeriod } from "@/lib/utils/chartData"
import { formatPercent } from "@/lib/utils/formatNumber"
import type { DivergencePoint, ReceivablesRatioPoint } from "@/types/analysis"

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend)

export interface RevenueQualityChartProps {
  divergences: DivergencePoint[];
  recvRatios: ReceivablesRatioPoint[];
  actions?: React.ReactNode;
}

export function RevenueQualityChart({ divergences, recvRatios, actions }: RevenueQualityChartProps) {
  if (divergences.length === 0 && recvRatios.length === 0) {
    return (
      <ChartFrame
        title="Revenue Quality"
        subtitle="Revenue / OCF divergence and receivables-to-revenue ratio"
        actions={actions}
      >
        <div className="flex items-center justify-center h-full font-sans text-sm text-text-muted text-center px-6">
          Not enough financial history to compute revenue-quality trends.
        </div>
      </ChartFrame>
    )
  }

  const { labels, data } = alignByPeriod([
    divergences.map((d) => ({ period: d.period, value: d.divergence })),
    recvRatios.map((r) => ({ period: r.period, value: r.recv_ratio })),
  ])

  const chartData = {
    labels,
    datasets: [
      {
        label: "Revenue / OCF Divergence",
        data: data[0],
        borderColor: colors.navy,
        backgroundColor: colors.navy,
        tension: 0,
        spanGaps: true,
      },
      {
        label: "Receivables / Revenue",
        data: data[1],
        borderColor: colors.risk.moderate,
        backgroundColor: colors.risk.moderate,
        tension: 0,
        spanGaps: true,
      },
    ],
  }

  const options = baseChartOptions<"line">(
    (v) => formatPercent(v, 0),
    (ctx) => `${ctx.dataset.label}: ${formatPercent(ctx.parsed.y, 1)}`
  )

  return (
    <ChartFrame
      title="Revenue Quality"
      subtitle="Revenue / OCF divergence and receivables-to-revenue ratio"
      actions={actions}
    >
      <Line data={chartData} options={options} />
    </ChartFrame>
  )
}
