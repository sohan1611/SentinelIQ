import * as React from "react";
import { IntegrityScoreGauge } from "@/components/charts/IntegrityGauge";
import { Badge } from "@/components/ui/Badge";
import { ModuleScoreCard } from "@/components/modules/ScoreCard";
import { RedFlagItem } from "@/components/modules/RedFlagItem";
import { RedFlagTimeline } from "@/components/charts/RedFlagTimeline";
import { NarrativeComparison } from "@/components/modules/NarrativeComparison";
import { SearchBar } from "@/components/layout/SearchBar";
import { CompanyCard } from "@/components/shared/CompanyCard";
import { RecommendationBox } from "@/components/modules/RecommendationBox";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";

// Helper component for the section header
function SectionHeader({ title }: { title: string }) {
  return (
    <div className="w-full bg-surface border border-border p-[16px] mb-8 mt-16 rounded-[4px]">
      <h2 className="font-sans text-[13px] font-semibold tracking-widest text-text-primary uppercase">
        {title}
      </h2>
    </div>
  );
}

// Helper component for variant labeling
function VariantBlock({ label, children, width = "auto" }: { label: string, children: React.ReactNode, width?: string }) {
  return (
    <div className={`flex flex-col p-[16px] items-center text-center ${width}`}>
      <div className="mb-4 w-full flex justify-center">
        {children}
      </div>
      <div className="font-sans text-[11px] text-text-secondary">
        {label}
      </div>
    </div>
  );
}

export default function DesignSystemPage() {
  return (
    <div className="min-h-screen bg-canvas p-10 font-sans">
      <div className="max-w-[1200px] mx-auto">
        <h1 className="font-serif text-4xl text-text-primary mb-2">SentinelIQ Component Library</h1>
        <p className="text-text-secondary text-sm mb-12">UI Primitives and Modules Reference Sheet</p>

        {/* 01 — INTEGRITY SCORE GAUGE */}
        <SectionHeader title="01 — INTEGRITY SCORE GAUGE" />
        <div className="flex flex-wrap items-end justify-start gap-8">
          <VariantBlock label="High Risk (31)">
            <IntegrityScoreGauge score={31} lastAnalyzed="June 9, 2025" />
          </VariantBlock>
          <VariantBlock label="Moderate Risk (52)">
            <IntegrityScoreGauge score={52} lastAnalyzed="June 9, 2025" />
          </VariantBlock>
          <VariantBlock label="Low Risk (78)">
            <IntegrityScoreGauge score={78} lastAnalyzed="June 9, 2025" />
          </VariantBlock>
          <VariantBlock label="Strong Integrity (91)">
            <IntegrityScoreGauge score={91} lastAnalyzed="June 9, 2025" />
          </VariantBlock>
          <VariantBlock label="Loading Skeleton">
            <IntegrityScoreGauge score={0} lastAnalyzed="June 9, 2025" loading={true} />
          </VariantBlock>
        </div>

        {/* 02 — RISK BADGES */}
        <SectionHeader title="02 — RISK BADGES" />
        <div className="flex flex-wrap items-center justify-start gap-8">
          <VariantBlock label="Severe Risk">
            <Badge risk="severe">Severe Risk</Badge>
          </VariantBlock>
          <VariantBlock label="High Risk">
            <Badge risk="high">High Risk</Badge>
          </VariantBlock>
          <VariantBlock label="Moderate Risk">
            <Badge risk="moderate">Moderate Risk</Badge>
          </VariantBlock>
          <VariantBlock label="Low Risk">
            <Badge risk="low">Low Risk</Badge>
          </VariantBlock>
          <VariantBlock label="Strong Integrity">
            <Badge risk="strong">Strong Integrity</Badge>
          </VariantBlock>
          <VariantBlock label="Analyzing...">
            <Badge risk="analyzing">Analyzing...</Badge>
          </VariantBlock>
          <VariantBlock label="Flagged Item">
            <Badge risk="flagged">Governance</Badge>
          </VariantBlock>
        </div>

        {/* 03 — MODULE SCORE CARDS */}
        <SectionHeader title="03 — MODULE SCORE CARDS" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <VariantBlock label="Moderate Risk (Amber)">
            <ModuleScoreCard label="Financial Quality" score={42} summary="Revenue growth diverging from operating cash flow for 3 consecutive quarters." />
          </VariantBlock>
          <VariantBlock label="High Risk (Red)">
            <ModuleScoreCard label="Cash Flow Integrity" score={31} summary="DSO increasing rapidly while inventory turnover drops." />
          </VariantBlock>
          <VariantBlock label="Low Risk (Navy)">
            <ModuleScoreCard label="Governance Risk" score={68} summary="Stable executive team with strong board independence metrics." />
          </VariantBlock>
          <VariantBlock label="Moderate Risk (Amber)">
            <ModuleScoreCard label="Narrative Consistency" score={55} summary="Shift in tone regarding future guidance detected in latest earnings call." />
          </VariantBlock>
        </div>

        {/* 04 — RED FLAG ITEMS */}
        <SectionHeader title="04 — RED FLAG ITEMS" />
        <div className="flex flex-col gap-4 max-w-[800px]">
          <VariantBlock label="Severe — Burgundy dot, Earnings Badge" width="w-full">
            <RedFlagItem severity="severe" date="Q3 2023" description="Massive unexpected write-down of inventory assets." type="Earnings" />
          </VariantBlock>
          <VariantBlock label="High — Red dot, Governance Badge" width="w-full">
            <RedFlagItem severity="high" date="Q1 2024" description="CFO resigned during fiscal year with no public explanation." type="Governance" />
          </VariantBlock>
          <VariantBlock label="Moderate — Amber dot, Cash Flow Badge" width="w-full">
            <RedFlagItem severity="moderate" date="Q2 2024" description="Operating cash flow lags net income by 25%." type="Cash Flow" />
          </VariantBlock>
        </div>

        {/* 05 — RED FLAG TIMELINE */}
        <SectionHeader title="05 — RED FLAG TIMELINE" />
        <VariantBlock label="Horizontal scrollable timeline with fade mask" width="w-full">
          <RedFlagTimeline events={[
            { id: "1", year: "Jan 2022", label: "Revenue Miss", severity: "moderate" },
            { id: "2", year: "Apr 2022", label: "CFO Resigned", severity: "high" },
            { id: "3", year: "Sep 2022", label: "Auditor Changed", severity: "high" },
            { id: "4", year: "Feb 2023", label: "Debt +43%", severity: "moderate" },
            { id: "5", year: "Jun 2023", label: "Guidance Cut", severity: "moderate" },
            { id: "6", year: "Nov 2023", label: "SEC Inquiry", severity: "severe" },
          ]} />
        </VariantBlock>

        {/* 06 — NARRATIVE COMPARISON */}
        <SectionHeader title="06 — NARRATIVE COMPARISON" />
        <div className="flex flex-col gap-12 max-w-[800px]">
          <VariantBlock label="Moderate Contradiction" width="w-full">
            <NarrativeComparison 
              left={{ period: "Q1 2023", quote: "Demand remains exceptionally strong across all markets.", sentiment: "OPTIMISTIC" }}
              right={{ period: "Q3 2023", quote: "Macroeconomic headwinds have materially weakened demand.", sentiment: "CAUTIONARY" }}
              contradictionAlert="Significant shift in tone detected across 2 quarters."
              alertSeverity="moderate"
            />
          </VariantBlock>
          <VariantBlock label="Severe Contradiction" width="w-full">
            <NarrativeComparison 
              left={{ period: "Q2 2023", quote: "We reiterate our full-year guidance of $1.2B in revenue.", sentiment: "OPTIMISTIC" }}
              right={{ period: "Q4 2023", quote: "We are withdrawing all prior financial guidance effective immediately.", sentiment: "CAUTIONARY" }}
              contradictionAlert="Prior guidance entirely withdrawn without preliminary warning."
              alertSeverity="severe"
            />
          </VariantBlock>
        </div>

        {/* 07 — SEARCH BAR */}
        <SectionHeader title="07 — SEARCH BAR" />
        <div className="flex flex-col gap-12 max-w-[800px]">
          <VariantBlock label="State 1: Empty / Default (Hero)" width="w-full">
            <SearchBar variant="hero" forceState="default" />
          </VariantBlock>
          <VariantBlock label="State 2: Focused (Hero)" width="w-full">
            <SearchBar variant="hero" forceState="focused" />
          </VariantBlock>
          <VariantBlock label="State 3: Typed input with populated dropdown (Hero)" width="w-full">
            <div className="h-[200px] w-full relative">
               <SearchBar variant="hero" forceState="typed" />
            </div>
          </VariantBlock>
          <VariantBlock label="State 4: Loading (Hero)" width="w-full">
            <SearchBar variant="hero" forceState="loading" />
          </VariantBlock>
          <VariantBlock label="Compact Variant (Default)" width="w-full">
            <SearchBar variant="compact" forceState="default" />
          </VariantBlock>
        </div>

        {/* 08 — COMPANY CARDS */}
        <SectionHeader title="08 — COMPANY CARDS" />
        <div className="flex flex-col gap-4 max-w-[800px]">
          <VariantBlock label="Watchlist Tile (Hover to see Action)" width="w-full">
            <CompanyCard name="Wirecard AG" ticker="WDI.DE" score={31} risk="high" lastAnalyzed="4 days ago" />
            <CompanyCard name="Apple Inc." ticker="AAPL" score={88} risk="strong" lastAnalyzed="1 day ago" />
            <CompanyCard name="Satyam Computer Services" ticker="SAY" score={24} risk="high" lastAnalyzed="2 weeks ago" />
            <CompanyCard name="Generic Co." ticker="GCO" score={56} risk="moderate" lastAnalyzed="3 hours ago" />
          </VariantBlock>
        </div>

        {/* 09 — RECOMMENDATION BOX */}
        <SectionHeader title="09 — RECOMMENDATION BOX" />
        <div className="flex flex-col gap-8 max-w-[800px]">
          <VariantBlock label="Standard Box" width="w-full">
            <RecommendationBox variant="standard" body={"Further investigation is advised before making investment or credit decisions.\nThe Corporate Integrity Score reflects publicly available information only\nand does not constitute financial advice."} />
          </VariantBlock>
          <VariantBlock label="Action Required Variant" width="w-full">
            <RecommendationBox variant="action-required" body={"Further investigation is advised before making investment or credit decisions.\nThe Corporate Integrity Score reflects publicly available information only\nand does not constitute financial advice."} />
          </VariantBlock>
        </div>

        {/* 10 — BUTTONS */}
        <SectionHeader title="10 — BUTTONS" />
        <div className="flex flex-col gap-12">
          <div className="flex flex-wrap items-center gap-8">
            <VariantBlock label="Primary Default">
              <Button variant="primary">Search</Button>
            </VariantBlock>
            <VariantBlock label="Primary Loading">
              <Button variant="primary" isLoading={true}>Search</Button>
            </VariantBlock>
            <VariantBlock label="Primary Disabled">
              <Button variant="primary" disabled={true}>Search</Button>
            </VariantBlock>
          </div>
          <div className="flex flex-wrap items-center gap-8">
            <VariantBlock label="Secondary Default">
              <Button variant="secondary">Export PDF Report</Button>
            </VariantBlock>
            <VariantBlock label="Secondary Disabled">
              <Button variant="secondary" disabled={true}>Export PDF Report</Button>
            </VariantBlock>
          </div>
          <div className="flex flex-wrap items-center gap-8">
            <VariantBlock label="Link Default">
              <Button variant="link">View Details →</Button>
            </VariantBlock>
            <VariantBlock label="Destructive Default">
              <Button variant="destructive">Remove from watchlist</Button>
            </VariantBlock>
          </div>
        </div>

        {/* 11 — SKELETON LOADERS */}
        <SectionHeader title="11 — SKELETON LOADERS" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <VariantBlock label="Module Score Card Skeleton" width="w-full">
            <ModuleScoreCard label="" score={0} summary="" loading={true} />
          </VariantBlock>
          <VariantBlock label="Red Flag Row Skeleton" width="w-full">
            <div className="w-full">
              <RedFlagItem severity="moderate" date="" description="" type="" loading={true} />
              <RedFlagItem severity="moderate" date="" description="" type="" loading={true} />
              <RedFlagItem severity="moderate" date="" description="" type="" loading={true} />
            </div>
          </VariantBlock>
        </div>

      </div>
    </div>
  );
}
