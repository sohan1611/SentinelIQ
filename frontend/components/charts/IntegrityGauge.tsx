"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import { Skeleton } from "../ui/Skeleton";
import { useReducedMotion } from "@/lib/hooks/useReducedMotion";

interface IntegrityGaugeProps {
  score: number;
  lastAnalyzed: string;
  loading?: boolean;
  startAnimation?: boolean;
}

function getRiskDetails(score: number) {
  if (score <= 20) return { color: "text-risk-severe", stroke: "stroke-risk-severe", label: "SEVERE RISK" };
  if (score <= 40) return { color: "text-risk-high", stroke: "stroke-risk-high", label: "HIGH RISK" };
  if (score <= 60) return { color: "text-risk-moderate", stroke: "stroke-risk-moderate", label: "MODERATE RISK" };
  if (score <= 80) return { color: "text-navy", stroke: "stroke-navy", label: "LOW RISK" };
  return { color: "text-risk-strong", stroke: "stroke-risk-strong", label: "STRONG INTEGRITY" };
}

export function IntegrityScoreGauge({ score, lastAnalyzed, loading, startAnimation = true }: IntegrityGaugeProps) {
  const [currentScore, setCurrentScore] = useState(0);
  const [isDone, setIsDone] = useState(false);
  const [arcProgress, setArcProgress] = useState(0);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (!startAnimation) {
      setCurrentScore(0);
      setArcProgress(0);
      setIsDone(false);
      return;
    }

    if (reducedMotion) {
      setCurrentScore(score);
      setArcProgress(score);
      setIsDone(true);
      return;
    }

    const duration = 700;
    const startTime = performance.now();
    let req: number;

    const animate = (time: number) => {
      const elapsed = time - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // --ease-out: cubic-bezier(0.0, 0.0, 0.2, 1.0) approximation (easeOutCirc / easeOutCubic)
      const easeOut = 1 - Math.pow(1 - progress, 3);
      
      setCurrentScore(Math.floor(easeOut * score));
      setArcProgress(easeOut * score);

      if (progress < 1) {
        req = requestAnimationFrame(animate);
      } else {
        setCurrentScore(score);
        setArcProgress(score);
        setTimeout(() => setIsDone(true), 50); // 50ms delay for text fade in
      }
    };

    req = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(req);
  }, [score, startAnimation, reducedMotion]);

  const risk = getRiskDetails(score);

  if (loading) {
    return (
      <div className="flex flex-col items-center">
        <div className="relative w-[140px] h-[140px] md:w-[200px] md:h-[200px] flex items-center justify-center mb-4">
          <Skeleton className="absolute w-full h-full rounded-full opacity-30" />
          <Skeleton className="w-[80px] h-[60px]" />
        </div>
        <Skeleton className="w-[120px] h-[16px]" />
      </div>
    );
  }

  const radius = 90; 
  const circumference = 2 * Math.PI * radius;
  const dasharray = `${circumference * 0.75} ${circumference * 0.25}`;
  
  // Base offset to start at bottom left
  const baseOffset = circumference * 0.625; 
  
  // The drawn length based on animated progress
  const drawnLength = circumference * 0.75 * (arcProgress / 100);
  
  // Set dasharray to the length we want drawn, followed by gap.
  // Actually, we can use dashoffset to reveal.
  const fillDasharray = `${drawnLength} ${circumference}`;

  return (
    <div
      className="flex flex-col items-center"
      role="meter"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={score}
      aria-valuetext={`${score} out of 100 — ${risk.label}`}
      aria-label="Corporate Integrity Score"
    >
      <div className="relative w-[140px] h-[140px] md:w-[200px] md:h-[200px] flex items-center justify-center">
        <svg
          aria-hidden="true"
          className="absolute top-0 left-0 w-full h-full transform -rotate-90"
          viewBox="0 0 200 200"
        >
          {/* Background Arc */}
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            className="stroke-[#E3DFD8]"
            strokeWidth="8"
            strokeDasharray={dasharray}
            strokeDashoffset={baseOffset}
            strokeLinecap="round"
          />
          {/* Foreground Arc */}
          {startAnimation && (
            <circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              className={risk.stroke}
              strokeWidth="8"
              strokeDasharray={fillDasharray}
              strokeDashoffset={baseOffset}
              strokeLinecap="round"
            />
          )}
        </svg>

        <div aria-hidden="true" className="flex flex-col items-center justify-center z-10 mt-4 md:mt-6">
          <div className={`font-mono text-[52px] md:text-[72px] font-bold leading-none ${risk.color}`}>
            {currentScore}
          </div>
          <div className="font-mono text-[14px] md:text-[18px] text-[#7A786F] mt-1">
            /100
          </div>
          
          <div 
            className={`font-sans text-[11px] font-medium uppercase tracking-[0.07em] mt-2 md:mt-3 ${risk.color}`}
            style={{
              opacity: isDone ? 1 : 0,
              transition: "opacity var(--duration-fast) var(--ease-out)"
            }}
          >
            {risk.label}
          </div>
        </div>
      </div>
      
      <div 
        className="font-sans text-[12px] text-[#7A786F] mt-6 md:mt-8"
        style={{
          opacity: isDone ? 1 : 0,
          transition: "opacity var(--duration-fast) var(--ease-out) 30ms"
        }}
      >
        Last analyzed: {lastAnalyzed}
      </div>
    </div>
  );
}
