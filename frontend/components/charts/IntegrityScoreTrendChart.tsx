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
import { Skeleton } from "@/components/ui/Skeleton"
import { colors } from "@/lib/theme/tokens"
import { baseChartOptions } from "@/lib/theme/chartOptions"
import { formatScore } from "@/lib/utils/formatNumber"
import { formatDate } from "@/lib/utils/formatDate"
import type { AnalysisHistoryItem } from "@/types/analysis"

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend)

export interface IntegrityScoreTrendChartProps {
  history: AnalysisHistoryItem[];
  isLoading?: boolean;
  actions?: React.ReactNode;
}

const TITLE = "Integrity Score Over Time"
const SUBTITLE = "Corporate Integrity Score across past analyses"

export function IntegrityScoreTrendChart({ history, isLoading, actions }: IntegrityScoreTrendChartProps) {
  if (isLoading) {
    return (
      <ChartFrame title={TITLE} subtitle={SUBTITLE} actions={actions}>
        <Skeleton className="w-full h-full" />
      </ChartFrame>
    )
  }

  if (history.length < 2) {
    return (
      <ChartFrame title={TITLE} subtitle={SUBTITLE} actions={actions}>
        <div className="flex items-center justify-center h-full font-sans text-sm text-text-muted text-center px-6">
          Run more analyses over time to see how this company&apos;s Integrity Score has changed.
        </div>
      </ChartFrame>
    )
  }

  const chartData = {
    labels: history.map((h) => formatDate(h.run_at)),
    datasets: [
      {
        label: "Integrity Score",
        data: history.map((h) => h.integrity_score),
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
    (v) => formatScore(v),
    (ctx) => `Integrity Score: ${formatScore(ctx.parsed.y)}`
  )
  options.scales!.y!.min = 0
  options.scales!.y!.max = 100

  return (
    <ChartFrame title={TITLE} subtitle={SUBTITLE} actions={actions}>
      <Line data={chartData} options={options} />
    </ChartFrame>
  )
}
