"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/types/api";
import { ROUTES } from "@/lib/constants/routes";

type State = "default" | "loading" | "error";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [state, setState] = useState<State>("default");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setState("loading");

    try {
      await login({ email, password });
      router.push(ROUTES.dashboard);
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setState("error");
    }
  };

  const isError = state === "error";
  const isLoading = state === "loading";

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

      <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[10px] p-[32px]">
        <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-[24px]">
          Sign in to SentinelIQ
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-[20px]">
          <div className="flex flex-col">
            <label htmlFor="login-email" className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Work Email
            </label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); if (state === "error") setState("default"); }}
              disabled={isLoading}
              placeholder="you@firm.com"
              aria-invalid={isError}
              aria-describedby={isError ? "login-error" : undefined}
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors disabled:bg-[#F6F4EF] ${
                isError
                  ? "border-[#B03028]"
                  : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
          </div>

          <div className="flex flex-col">
            <div className="flex justify-between items-center mb-[6px]">
              <label htmlFor="login-password" className="font-sans text-[12px] font-semibold text-[#1A1A18]">
                Password
              </label>
              <Link href="/forgot-password" className="font-sans text-[11px] text-[#1C3558] hover:underline">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => { setPassword(e.target.value); if (state === "error") setState("default"); }}
                disabled={isLoading}
                placeholder="············"
                aria-invalid={isError}
                aria-describedby={isError ? "login-error" : undefined}
                className={`w-full h-[44px] pl-3 pr-12 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors duration-fast ease-out disabled:bg-[#F6F4EF] ${!showPassword ? 'tracking-widest' : ''} ${
                  isError
                    ? "border-[#B03028]"
                    : "border-[#E3DFD8] focus:border-[#1C3558]"
                }`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 font-sans text-[12px] text-[#1C3558] select-none hover:underline focus-visible:outline-none focus-visible:underline"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            {isError && (
              <span id="login-error" className="font-sans text-[12px] text-[#B03028] mt-[4px] tracking-normal transition-all duration-fast ease-out">
                {errorMessage}
              </span>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full mt-[4px]"
            isLoading={isLoading}
            loadingText="Signing in..."
          >
            Sign In
          </Button>
        </form>
      </div>

      <div className="text-center mt-[20px]">
        <span className="font-sans text-[13px] text-[#7A786F]">
          Don&apos;t have an account?{" "}
        </span>
        <Link href="/register" className="font-sans text-[13px] text-[#1C3558] hover:underline">
          Get started →
        </Link>
      </div>
    </div>
  );
}
