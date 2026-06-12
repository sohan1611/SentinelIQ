"use client";

import React from "react";
import { Badge } from "@/components/ui/Badge";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
} from "chart.js";
import { Line, Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler, Tooltip);

const commonOptions = {
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
      displayColors: true,
    },
  },
  scales: {
    x: {
      grid: { display: false, drawBorder: false },
      ticks: { font: { family: "IBM Plex Mono", size: 11 }, color: "#7A786F" },
    },
    y: {
      grid: { color: "#E3DFD8", drawBorder: false }, // faint horizontal rules
      border: { dash: [4, 4] },
      ticks: { font: { family: "IBM Plex Mono", size: 11 }, color: "#7A786F" },
    },
  },
};

export default function FinancialsPage() {
  const revenueChartData = {
    labels: ["Q1 2021", "Q2 2021", "Q3 2021", "Q4 2021", "Q1 2022", "Q2 2022", "Q3 2022", "Q4 2022", "Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023"],
    datasets: [
      {
        label: "Revenue Growth %",
        data: [12, 15, 18, 22, 25, 28, 30, 34, 35, 36, 36, 38],
        borderColor: "#1C3558",
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.3,
      },
      {
        label: "Operating Cash Flow Growth %",
        data: [10, 14, 15, 18, 14, 8, 2, -5, -12, -15, -18, -22],
        borderColor: "#C47A14",
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.3,
      },
    ],
  };

  const cashFlowChartData = {
    labels: ["FY2020", "FY2021", "FY2022", "FY2023"],
    datasets: [
      {
        label: "Net Income",
        data: [150, 180, 240, 280],
        backgroundColor: "#1C3558",
        borderRadius: { topLeft: 4, topRight: 4, bottomLeft: 0, bottomRight: 0 },
        barPercentage: 0.6,
        categoryPercentage: 0.8,
      },
      {
        label: "Operating Cash Flow",
        data: [140, 160, -40, -110],
        backgroundColor: "#B03028",
        borderRadius: { topLeft: 4, topRight: 4, bottomLeft: 0, bottomRight: 0 },
        barPercentage: 0.6,
        categoryPercentage: 0.8,
      },
    ],
  };

  const debtStressChartData = {
    labels: ["Q1 2021", "Q2 2021", "Q3 2021", "Q4 2021", "Q1 2022", "Q2 2022", "Q3 2022", "Q4 2022", "Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023"],
    datasets: [
      {
        label: "Debt-to-Revenue Ratio",
        data: [0.4, 0.45, 0.5, 0.55, 0.6, 0.8, 0.95, 1.1, 1.25, 1.35, 1.5, 1.6],
        borderColor: "#B03028",
        backgroundColor: "#FAE8E8",
        fill: true,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.3,
      },
    ],
  };

  return (
    <div className="w-full flex flex-col gap-12 mt-8 pb-16">
      
      {/* SECTION A: Revenue Quality Analysis */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">
            REVENUE QUALITY
          </h2>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[13px] font-medium text-[#C47A14]">42 / 100</span>
            <Badge risk="moderate">MODERATE</Badge>
          </div>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-[20px] mb-4 h-[240px]">
          <div className="h-[180px] w-full">
            <Line data={revenueChartData} options={commonOptions} />
          </div>
          <div className="mt-2 flex items-center justify-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#1C3558]" />
              <span className="font-sans text-[11px] text-[#7A786F]">Revenue Growth %</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#C47A14]" />
              <span className="font-sans text-[11px] text-[#7A786F]">Operating Cash Flow Growth %</span>
            </div>
          </div>
        </div>

        <p className="font-sans text-[14px] text-[#1A1A18] leading-[1.65] max-w-[800px]">
          Revenue grew 34% year-over-year in FY2022 while operating cash flow declined 18% over the same period — a divergence inconsistent with genuine organic growth.
        </p>
      </section>

      {/* SECTION B: Cash Flow Integrity */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">
            CASH FLOW INTEGRITY
          </h2>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[13px] font-medium text-[#B03028]">31 / 100</span>
            <Badge risk="high">HIGH RISK</Badge>
          </div>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-[20px] mb-4 h-[240px]">
          <div className="h-[180px] w-full">
            <Bar data={cashFlowChartData} options={commonOptions} />
          </div>
          <div className="mt-2 flex items-center justify-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#1C3558]" />
              <span className="font-sans text-[11px] text-[#7A786F]">Net Income</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#B03028]" />
              <span className="font-sans text-[11px] text-[#7A786F]">Operating Cash Flow</span>
            </div>
          </div>
        </div>

        <p className="font-sans text-[14px] text-[#1A1A18] leading-[1.65] max-w-[800px]">
          Net income exceeded operating cash flow by an average of 40% over four consecutive fiscal years — a pattern consistent with aggressive accruals accounting.
        </p>
      </section>

      {/* SECTION C: Debt Stress Analysis */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <h2 className="font-sans text-[10px] font-medium uppercase tracking-[0.08em] text-[#7A786F]">
            DEBT STRESS
          </h2>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[13px] font-medium text-[#B03028]">28 / 100</span>
            <Badge risk="high">HIGH RISK</Badge>
          </div>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-[20px] mb-4 h-[240px]">
          <div className="h-[180px] w-full relative">
            <Line data={debtStressChartData} options={commonOptions} />
            {/* Custom Threshold Line Overlay */}
            <div className="absolute top-1/2 left-0 right-0 h-[1px] border-t border-dashed border-[#E3DFD8] flex items-center pointer-events-none" style={{ top: '65%' }}>
               <span className="bg-[#FFFFFF] px-2 text-[10px] font-sans text-[#B0ADA7] uppercase tracking-[0.04em] relative -top-[8px] left-4">Threshold</span>
            </div>
          </div>
          <div className="mt-2 flex items-center justify-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#B03028]" />
              <span className="font-sans text-[11px] text-[#7A786F]">Debt-to-Revenue Ratio</span>
            </div>
          </div>
        </div>

        <p className="font-sans text-[14px] text-[#1A1A18] leading-[1.65] max-w-[800px]">
          Total debt obligations have expanded significantly faster than top-line revenue, surpassing the 1.0 threshold in Q4 2022 and indicating elevated liquidity risk.
        </p>
      </section>

    </div>
  );
}
