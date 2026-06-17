"use client";

import React, { createContext, useContext } from "react";
import type { Company } from "@/types/company";
import type { AnalysisResultWithFlags, AnalysisStatus } from "@/types/analysis";

interface CompanyContextValue {
  company: Company | null;
  analysis: AnalysisResultWithFlags | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
  analysisStatus: AnalysisStatus | null;
  isRunning: boolean;
  analysisError: string | null;
  startAnalysis: (ticker: string) => Promise<void>;
}

export const CompanyContext = createContext<CompanyContextValue | undefined>(undefined);

export function useCompanyContext(): CompanyContextValue {
  const ctx = useContext(CompanyContext);
  if (!ctx) throw new Error("useCompanyContext must be used inside CompanyLayout");
  return ctx;
}
