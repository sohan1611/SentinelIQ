"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#F6F4EF] flex flex-col items-center justify-center p-4">
      <div className="flex flex-col items-center justify-center text-center w-full max-w-[400px]">
        
        <div className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-12">
          SentinelIQ
        </div>

        <div className="font-mono text-[96px] font-bold text-[#E3DFD8] leading-none mb-6">
          500
        </div>

        <h1 className="font-sans text-[20px] font-semibold text-[#1A1A18] mb-4">
          Something went wrong.
        </h1>

        <p className="font-sans text-[14px] text-[#7A786F] max-w-[380px] mx-auto mb-8 leading-[1.6]">
          We encountered an unexpected error. Our team has been notified. Please try again in a moment.
        </p>

        <div className="flex flex-col items-center gap-4 w-full">
          <Button variant="primary" onClick={() => reset()} className="w-[140px]">
            Try Again
          </Button>
          <span className="font-sans text-[12px] text-[#B0ADA7] mt-2">
            If this persists, contact support@sentineliq.io
          </span>
        </div>

      </div>
    </div>
  );
}
