"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import { NarrativeComparison } from "@/components/modules/NarrativeComparison";
import { Line } from "react-chartjs-2";

export default function NarrativePage() {
  const chartData = {
    labels: ["Q1 2021", "Q2 2021", "Q3 2021", "Q4 2021", "Q1 2022", "Q2 2022", "Q3 2022", "Q4 2022", "Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023"],
    datasets: [
      {
        label: "Confidence Score %",
        data: [88, 86, 85, 80, 82, 75, 60, 45, 55, 30, 25, 15],
        borderColor: "#1C3558",
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.4, // smooth curve
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#FFFFFF",
        titleColor: "#1A1A18",
        bodyColor: "#1A1A18",
        borderColor: "#E3DFD8",
        borderWidth: 1,
        titleFont: { family: "Inter", size: 12 },
        bodyFont: { family: "IBM Plex Mono", size: 12 },
        padding: 10,
        cornerRadius: 4,
        displayColors: false,
      },
      annotation: {
        // Since we don't have chartjs-plugin-annotation installed by default, 
        // we will manually render the annotations as absolute positioned divs,
        // or just let the tooltip serve the purpose for now. 
      }
    },
    scales: {
      x: {
        grid: { display: false, drawBorder: false },
        ticks: { font: { family: "IBM Plex Mono", size: 11 }, color: "#7A786F" },
      },
      y: {
        grid: { color: "#E3DFD8", drawBorder: false },
        border: { dash: [4, 4] },
        ticks: { font: { family: "IBM Plex Mono", size: 11 }, color: "#7A786F" },
        min: 0,
        max: 100,
      },
    },
  };

  return (
    <div className="w-full flex flex-col gap-12 mt-8 pb-16">
      
      {/* SCORE PANEL */}
      <section>
        <div className="flex items-center gap-3 mb-3">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">
            NARRATIVE CONSISTENCY
          </h2>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[13px] font-medium text-[#C47A14]">55 / 100</span>
            <Badge risk="moderate">MODERATE RISK</Badge>
          </div>
        </div>
        <p className="font-sans text-[14px] text-[#1A1A18] leading-[1.65]">
          Significant tone shift and contradictory guidance statements detected across Q1 2022 to Q4 2023.
        </p>
      </section>

      {/* COMPARISON BLOCKS */}
      <section className="flex flex-col gap-10">
        <NarrativeComparison 
          left={{
            period: "Q1 2022",
            sentiment: "OPTIMISTIC",
            quote: "Demand remains exceptionally strong across all markets. We see no slowdown on the horizon."
          }}
          right={{
            period: "Q3 2022",
            sentiment: "CAUTIONARY",
            quote: "Macroeconomic headwinds have materially weakened near-term demand across key segments."
          }}
          contradictionAlert="Significant shift in tone detected across 2 quarters."
          alertSeverity="moderate"
        />

        <NarrativeComparison 
          left={{
            period: "Q2 2022",
            sentiment: "OPTIMISTIC",
            quote: "We reaffirm full-year revenue guidance of €5.4B with high confidence."
          }}
          right={{
            period: "Q4 2022",
            sentiment: "CAUTIONARY",
            quote: "Given evolving market conditions, we are withdrawing forward guidance for FY2023."
          }}
          contradictionAlert="Guidance withdrawn 2 quarters after reaffirmation."
          alertSeverity="severe"
        />

        <NarrativeComparison 
          left={{
            period: "Q1 2023",
            sentiment: "OPTIMISTIC",
            quote: "Our balance sheet remains robust with €1.9B in cash and liquid assets."
          }}
          right={{
            period: "Q2 2023",
            sentiment: "CAUTIONARY",
            quote: "A cash shortfall has been identified following an internal audit review."
          }}
          contradictionAlert="Material cash discrepancy emerged within one quarter."
          alertSeverity="severe"
        />
      </section>

      {/* SENTIMENT TREND CHART */}
      <section>
        <div className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F] mb-6">
          MANAGEMENT SENTIMENT OVER TIME
        </div>

        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-[20px] h-[300px] relative">
          <Line data={chartData} options={chartOptions} />
          
          {/* Custom Annotations (Positioned Manually for visual effect) */}
          <div className="absolute flex flex-col items-center" style={{ left: '65%', top: '55%' }}>
            <div className="w-2 h-2 rounded-full bg-[#B03028]" />
            <div className="mt-1 font-sans text-[10px] text-[#B03028]">Guidance withdrawn</div>
          </div>
          <div className="absolute flex flex-col items-center" style={{ left: '80%', top: '70%' }}>
            <div className="w-2 h-2 rounded-full bg-[#B03028]" />
            <div className="mt-1 font-sans text-[10px] text-[#B03028]">Audit review</div>
          </div>
        </div>
      </section>

    </div>
  );
}
