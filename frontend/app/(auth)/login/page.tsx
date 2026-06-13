"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

type State = "default" | "loading" | "error";

export default function LoginPage() {
  const [state, setState] = useState<State>("default");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setState("loading");
    // Simulate network request then fail to show error state as requested
    setTimeout(() => {
      setState("error");
    }, 1500);
  };

  const isError = state === "error";
  const isLoading = state === "loading";

  return (
    <div className="w-full">
      {/* State Toggle for Review Purposes */}
      <div className="absolute top-4 right-4 flex gap-2">
        <button onClick={() => setState("default")} className="text-xs text-gray-500">Default</button>
        <button onClick={() => setState("error")} className="text-xs text-red-500">Error</button>
        <button onClick={() => setState("loading")} className="text-xs text-blue-500">Loading</button>
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
        <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-[24px]">
          Sign in to SentinelIQ
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-[20px]">
          <div className="flex flex-col">
            <label className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Work Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              placeholder="you@firm.com"
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors disabled:bg-[#F6F4EF] ${
                isError 
                  ? "border-[#B03028]" 
                  : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
            {isError && (
              <span className="font-sans text-[12px] text-[#B03028] mt-[4px]">
                No account found with this email address.
              </span>
            )}
          </div>

          <div className="flex flex-col">
            <div className="flex justify-between items-center mb-[6px]">
              <label className="font-sans text-[12px] font-semibold text-[#1A1A18]">
                Password
              </label>
              <Link href="/forgot-password" className="font-sans text-[11px] text-[#1C3558] hover:underline">
                Forgot password?
              </Link>
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              placeholder="············"
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors disabled:bg-[#F6F4EF] tracking-widest ${
                isError 
                  ? "border-[#B03028]" 
                  : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
            {isError && (
              <span className="font-sans text-[12px] text-[#B03028] mt-[4px] tracking-normal">
                Password is incorrect.
              </span>
            )}
          </div>

          <Button 
            type="submit" 
            variant="primary" 
            className="w-full mt-[4px]"
            disabled={isLoading}
          >
            {isLoading ? "Signing in..." : "Sign In"}
          </Button>
        </form>
      </div>

      <div className="text-center mt-[20px]">
        <span className="font-sans text-[13px] text-[#7A786F]">
          Don't have an account?{" "}
        </span>
        <Link href="/register" className="font-sans text-[13px] text-[#1C3558] hover:underline">
          Get started →
        </Link>
      </div>
    </div>
  );
}
