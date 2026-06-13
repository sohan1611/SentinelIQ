"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

type VerifyState = "verifying" | "success" | "invalid";

export default function VerifyEmailPage() {
  const [state, setState] = useState<VerifyState>("verifying");

  return (
    <div className="w-full relative">
      {/* State Toggle for Review Purposes */}
      <div className="absolute -top-10 right-0 flex gap-2">
        <button onClick={() => setState("verifying")} className="text-xs text-blue-500">Verifying</button>
        <button onClick={() => setState("success")} className="text-xs text-green-500">Success</button>
        <button onClick={() => setState("invalid")} className="text-xs text-red-500">Invalid</button>
      </div>

      <div className="flex flex-col items-center mb-[32px]">
        <h1 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-1">
          SentinelIQ
        </h1>
        {state === "verifying" && (
          <p className="font-sans text-[15px] text-[#7A786F] mt-6 mb-8">
            Verifying your account...
          </p>
        )}
      </div>

      {state === "verifying" && (
        <div className="flex justify-center w-full">
          <div className="w-[200px] h-[2px] bg-[#E3DFD8] relative overflow-hidden">
            <div className="absolute top-0 left-0 h-full w-[40px] bg-[#1C3558] animate-[slideRight_1.5s_infinite_ease-in-out]" />
          </div>
          <style dangerouslySetInnerHTML={{__html: `
            @keyframes slideRight {
              0% { left: -40px; }
              100% { left: 200px; }
            }
          `}} />
        </div>
      )}

      {state === "success" && (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[10px] p-[32px] flex flex-col items-center text-center">
          <div className="font-sans text-[32px] text-[#1A6B3C] mb-4 leading-none">✓</div>
          <h2 className="font-sans text-[20px] font-semibold text-[#1A1A18] mb-2">
            Your account is verified.
          </h2>
          <p className="font-sans text-[14px] text-[#7A786F] mb-8">
            You can now sign in to SentinelIQ.
          </p>
          <Link href="/dashboard" className="w-[200px]">
            <Button variant="primary" className="w-full">
              Go to Dashboard
            </Button>
          </Link>
        </div>
      )}

      {state === "invalid" && (
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[10px] p-[32px] flex flex-col items-center text-center">
          <h2 className="font-sans text-[20px] font-semibold text-[#1A1A18] mb-2">
            Link expired or invalid.
          </h2>
          <p className="font-sans text-[14px] text-[#7A786F] mb-8 max-w-[280px]">
            This verification link is no longer valid. Request a new one below.
          </p>
          <div className="w-[240px]">
            <Button variant="secondary" className="w-full">
              Resend Verification Email
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
