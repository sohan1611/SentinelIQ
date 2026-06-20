"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function ForgotPasswordPage() {
  const [isSent, setIsSent] = useState(false);
  const [email, setEmail] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSent(true);
  };

  if (isSent) {
    return (
      <div className="w-full relative">
        <div className="absolute -top-10 right-0 flex gap-2">
          <button onClick={() => setIsSent(false)} className="text-xs text-gray-500">Default</button>
          <button onClick={() => setIsSent(true)} className="text-xs text-green-500">Sent</button>
        </div>

        <div className="flex flex-col items-center mb-[32px]">
          <h1 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-1">
            SentinelIQ
          </h1>
          <p className="font-sans text-[12px] text-[#B0ADA7]">
            Corporate fraud intelligence.
          </p>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[10px] p-[32px] flex flex-col items-center text-center">
          <div className="font-sans text-[28px] text-[#1A6B3C] mb-4 leading-none">✓</div>
          <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-2">
            Reset link sent.
          </h2>
          <p className="font-sans text-[13px] text-[#7A786F] mb-6 max-w-[280px]">
            If {email || "jane@firm.com"} has an account, you&apos;ll receive an email within 2 minutes.
          </p>
          <p className="font-sans text-[12px] text-[#B0ADA7] italic">
            Didn&apos;t receive it? Check your spam folder.
          </p>
        </div>
        
        <div className="text-center mt-[20px]">
          <span className="font-sans text-[13px] text-[#7A786F]">
            Back to{" "}
          </span>
          <Link href="/login" className="font-sans text-[13px] text-[#1C3558] hover:underline">
            sign in →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full relative">
      {/* State Toggle for Review Purposes */}
      <div className="absolute -top-10 right-0 flex gap-2">
        <button onClick={() => setIsSent(false)} className="text-xs text-gray-500">Default</button>
        <button onClick={() => setIsSent(true)} className="text-xs text-green-500">Sent</button>
      </div>

      <div className="flex flex-col items-center mb-[32px]">
        <h1 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-1">
          SentinelIQ
        </h1>
        <p className="font-sans text-[12px] text-[#B0ADA7]">
          Corporate fraud intelligence.
        </p>
      </div>

      <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[10px] p-[32px]">
        <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-[8px]">
          Reset your password
        </h2>
        <p className="font-sans text-[13px] text-[#7A786F] mb-[24px]">
          Enter your email and we&apos;ll send a reset link.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-[20px]">
          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Work Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@firm.com"
              className="h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border border-[#E3DFD8] focus:border-[#1C3558] rounded-[6px] outline-none transition-colors"
              required
            />
          </div>

          <Button type="submit" variant="primary" className="w-full mt-2">
            Send Reset Link
          </Button>
        </form>
      </div>

      <div className="text-center mt-[20px]">
        <span className="font-sans text-[13px] text-[#7A786F]">
          Back to{" "}
        </span>
        <Link href="/login" className="font-sans text-[13px] text-[#1C3558] hover:underline">
          sign in →
        </Link>
      </div>
    </div>
  );
}
