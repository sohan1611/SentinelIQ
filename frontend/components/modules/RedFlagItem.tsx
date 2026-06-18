"use client";

import * as React from "react";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Modal } from "../ui/Modal";
import { Skeleton } from "../ui/Skeleton";
import { useToast } from "@/contexts/ToastContext";
import { reportAnalysisError } from "@/lib/api/feedback";

export type Severity = "severe" | "high" | "moderate";

export interface EvidenceRow {
  label: string;
  value: string;
}

interface RedFlagItemProps {
  severity: Severity;
  date: string;
  description: string;
  type: string;
  loading?: boolean;
  evidence?: EvidenceRow[];
  analysisId?: string;
  flagId?: string;
}

export function RedFlagItem({
  severity,
  date,
  description,
  type,
  loading,
  evidence = [],
  analysisId,
  flagId,
}: RedFlagItemProps) {
  const { showToast } = useToast();
  const [expanded, setExpanded] = React.useState(false);
  const [reportOpen, setReportOpen] = React.useState(false);
  const [message, setMessage] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);

  if (loading) {
    return (
      <div className="flex items-center w-full py-3 border-b border-border">
        <Skeleton className="w-2 h-2 rounded-full mr-4" />
        <Skeleton className="w-[80px] h-4 mr-4" />
        <Skeleton className="flex-1 h-4 mr-4" />
        <Skeleton className="w-[80px] h-5 rounded-[4px]" />
      </div>
    );
  }

  const dotColors = {
    severe: "bg-risk-severe",
    high: "bg-risk-high",
    moderate: "bg-risk-moderate",
  };

  const hasEvidence = evidence.length > 0;
  const canReport = !!analysisId;

  const handleSubmit = async () => {
    if (!analysisId || !message.trim()) return;
    setSubmitting(true);
    try {
      await reportAnalysisError({
        analysis_id: analysisId,
        flag_id: flagId,
        message: message.trim(),
      });
      showToast("Feedback received. Thank you.", "success");
      setReportOpen(false);
      setMessage("");
    } catch {
      showToast("Failed to submit feedback. Please try again.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="border-b border-border">
        <div
          className="group flex items-center w-full py-3 hover:bg-[#F1EFE9] transition-colors bg-transparent px-2 -mx-2"
          style={{ cursor: hasEvidence ? "pointer" : "default" }}
          onClick={hasEvidence ? () => setExpanded((v) => !v) : undefined}
        >
          <div className={`w-2 h-2 rounded-full shrink-0 mr-4 ${dotColors[severity]}`} />
          <div className="font-mono text-[12px] text-text-secondary w-[80px] shrink-0">
            {date}
          </div>
          <div className="font-sans text-[14px] text-text-primary flex-1 truncate pr-4">
            {description}
          </div>
          <div className="shrink-0 flex items-center gap-3">
            {hasEvidence && (
              <span className="font-sans text-[11px] text-[#1C3558] hover:underline">
                {expanded ? "Hide" : "Evidence"}
              </span>
            )}
            <Badge risk="flagged">{type}</Badge>
          </div>
        </div>

        {expanded && hasEvidence && (
          <div className="flex flex-col gap-1 pb-3 pl-6 pr-2">
            {evidence.map((row) => (
              <div key={row.label} className="flex justify-between max-w-[320px]">
                <span className="font-sans text-[12px] text-text-secondary">{row.label}</span>
                <span className="font-mono text-[12px] text-text-primary">{row.value}</span>
              </div>
            ))}
          </div>
        )}

        {canReport && (
          <div className="pb-2 pl-6 pr-2">
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); setReportOpen(true); }}
              className="font-sans text-[10px] text-[#B0ADA7] hover:text-[#7A786F] transition-colors"
            >
              Report an issue
            </button>
          </div>
        )}
      </div>

      <Modal
        isOpen={reportOpen}
        onClose={() => { setReportOpen(false); setMessage(""); }}
        title="Report an issue"
        size="sm"
        footer={
          <>
            <button
              type="button"
              onClick={() => { setReportOpen(false); setMessage(""); }}
              className="font-sans text-[13px] text-text-secondary hover:text-text-primary transition-colors"
            >
              Cancel
            </button>
            <Button
              variant="primary"
              onClick={handleSubmit}
              isLoading={submitting}
              loadingText="Sending..."
              disabled={!message.trim() || submitting}
            >
              Submit
            </Button>
          </>
        }
      >
        <p className="font-sans text-[13px] text-text-secondary mb-4">
          Describe the issue with this flag — e.g. it appears incorrect, outdated, or misleading.
        </p>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          maxLength={1000}
          rows={4}
          placeholder="Describe the issue..."
          className="w-full px-3 py-2 font-sans text-[14px] text-text-primary placeholder:text-[#B0ADA7] bg-white border border-border rounded-[6px] outline-none focus:border-[#1C3558] resize-none transition-colors"
        />
        <div className="font-sans text-[11px] text-[#B0ADA7] text-right mt-1">
          {message.length}/1000
        </div>
      </Modal>
    </>
  );
}
