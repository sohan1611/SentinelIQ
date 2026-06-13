"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

type State = "default" | "error" | "success";

export default function RegisterPage() {
  const [state, setState] = useState<State>("default");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setState("success");
  };

  const isError = state === "error";

  if (state === "success") {
    return (
      <div className="w-full">
        <div className="flex flex-col items-center mb-[32px]">
          <h1 className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-1">
            SentinelIQ
          </h1>
          <p className="font-sans text-[12px] text-[#B0ADA7]">
            Corporate fraud intelligence.
          </p>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[10px] p-[32px] flex flex-col items-center text-center">
          <div className="font-sans text-[32px] text-[#1A6B3C] mb-4 leading-none">✓</div>
          <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-2">
            Check your inbox.
          </h2>
          <p className="font-sans text-[14px] text-[#7A786F] mb-6 max-w-[280px]">
            We sent a verification link to jane@firm.com. Click the link to activate your account.
          </p>
          <button className="font-sans text-[14px] text-[#1C3558] hover:underline" onClick={() => setState("default")}>
            Resend email
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full relative">
      {/* State Toggle for Review Purposes */}
      <div className="absolute -top-10 right-0 flex gap-2">
        <button onClick={() => setState("default")} className="text-xs text-gray-500">Default</button>
        <button onClick={() => setState("error")} className="text-xs text-red-500">Error</button>
        <button onClick={() => setState("success")} className="text-xs text-green-500">Success</button>
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
          Create your account
        </h2>
        <p className="font-sans text-[13px] text-[#7A786F] mb-[24px]">
          Free to start. No credit card required.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-[20px]">
          
          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jane Smith"
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors ${
                isError ? "border-[#B03028]" : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
            {isError && <span className="font-sans text-[12px] text-[#B03028] mt-[4px]">Please enter your full name.</span>}
          </div>

          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Work Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@firm.com"
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors ${
                isError ? "border-[#B03028]" : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
            {isError && <span className="font-sans text-[12px] text-[#B03028] mt-[4px]">Enter a valid work email address.</span>}
          </div>

          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min. 8 characters"
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors tracking-widest ${
                isError ? "border-[#B03028]" : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
            {isError && <span className="font-sans text-[12px] text-[#B03028] mt-[4px] tracking-normal">Password must be at least 8 characters.</span>}
          </div>

          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Repeat password"
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors tracking-widest ${
                isError ? "border-[#B03028]" : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
            {isError && <span className="font-sans text-[12px] text-[#B03028] mt-[4px] tracking-normal">Passwords do not match.</span>}
          </div>

          <div className="flex items-start mt-2">
            <div className="flex items-center h-5">
              <input
                id="terms"
                type="checkbox"
                className="w-4 h-4 bg-[#FFFFFF] border-[#E3DFD8] rounded-[4px] accent-[#1C3558] cursor-pointer"
              />
            </div>
            <div className="ml-3 font-sans text-[12px] text-[#7A786F]">
              I agree to the <Link href="#" className="text-[#1C3558]">Terms of Service</Link> and <Link href="#" className="text-[#1C3558]">Privacy Policy</Link>.
            </div>
          </div>

          <Button type="submit" variant="primary" className="w-full mt-2">
            Create Account
          </Button>
        </form>
      </div>

      <div className="text-center mt-[20px]">
        <span className="font-sans text-[13px] text-[#7A786F]">
          Already have an account?{" "}
        </span>
        <Link href="/login" className="font-sans text-[13px] text-[#1C3558] hover:underline">
          Sign in →
        </Link>
      </div>
    </div>
  );
}
