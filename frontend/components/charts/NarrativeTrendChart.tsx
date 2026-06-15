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
import type { NarrativeSnapshotData } from "@/types/analysis"

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend)

export interface NarrativeTrendChartProps {
  snapshots: NarrativeSnapshotData[];
  actions?: React.ReactNode;
}

export function NarrativeTrendChart({ snapshots, actions }: NarrativeTrendChartProps) {
  if (snapshots.length === 0) {
    return (
      <ChartFrame
        title="Management Sentiment Over Time"
        subtitle="Sentiment score derived from management commentary, per reporting period"
        actions={actions}
      >
        <div className="flex items-center justify-center h-full font-sans text-sm text-text-muted text-center px-6">
          Not enough management commentary to compute a sentiment trend.
        </div>
      </ChartFrame>
    )
  }

  const { labels, data } = alignByPeriod([
    snapshots.map((s) => ({ period: s.period, value: s.sentiment_score })),
  ])

  const chartData = {
    labels,
    datasets: [
      {
        label: "Sentiment Score",
        data: data[0],
        borderColor: colors.navy,
        backgroundColor: colors.navy,
        pointRadius: 3,
        pointHoverRadius: 4,
        tension: 0,
        spanGaps: true,
      },
    ],
  }

  const options = baseChartOptions<"line">(
    (v) => formatPercent(v, 0),
    (ctx) => `Sentiment: ${formatPercent(ctx.parsed.y, 0)}`
  )

  return (
    <ChartFrame
      title="Management Sentiment Over Time"
      subtitle="Sentiment score derived from management commentary, per reporting period"
      actions={actions}
    >
      <Line data={chartData} options={options} />
    </ChartFrame>
  )
}
