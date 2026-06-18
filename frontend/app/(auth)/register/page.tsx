"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/types/api";
import { ROUTES } from "@/lib/constants/routes";

type State = "default" | "loading" | "error";

interface FieldErrors {
  name?: string;
  email?: string;
  password?: string;
  confirm?: string;
  terms?: string;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [state, setState] = useState<State>("default");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const errors: FieldErrors = {};
    if (!name.trim()) errors.name = "Please enter your full name.";
    if (!EMAIL_PATTERN.test(email)) errors.email = "Enter a valid work email address.";
    if (password.length < 8) errors.password = "Password must be at least 8 characters.";
    if (confirm !== password) errors.confirm = "Passwords do not match.";
    if (!agreed) errors.terms = "You must agree to the terms to continue.";

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setErrorMessage("");
      setState("error");
      return;
    }

    setFieldErrors({});
    setErrorMessage("");
    setState("loading");

    try {
      await register({ email, password, full_name: name });
      router.push(ROUTES.dashboard);
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setState("error");
    }
  };

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
        <h2 className="font-sans text-[18px] font-semibold text-[#1A1A18] mb-[8px]">
          Create your account
        </h2>
        <p className="font-sans text-[13px] text-[#7A786F] mb-[24px]">
          Free to start. No credit card required.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-[20px]">

          <div className="flex flex-col">
            <label htmlFor="reg-name" className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Full Name
            </label>
            <input
              id="reg-name"
              type="text"
              value={name}
              onChange={(e) => { setName(e.target.value); if (errorMessage) setErrorMessage(""); }}
              disabled={isLoading}
              placeholder="Jane Smith"
              aria-invalid={!!fieldErrors.name}
              aria-describedby={fieldErrors.name ? "reg-name-error" : undefined}
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors disabled:bg-[#F6F4EF] ${
                fieldErrors.name ? "border-[#B03028]" : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
            {fieldErrors.name && (
              <span id="reg-name-error" className="font-sans text-[12px] text-[#B03028] mt-[4px]">{fieldErrors.name}</span>
            )}
          </div>

          <div className="flex flex-col">
            <label htmlFor="reg-email" className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Work Email
            </label>
            <input
              id="reg-email"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); if (errorMessage) setErrorMessage(""); }}
              disabled={isLoading}
              placeholder="you@firm.com"
              aria-invalid={!!fieldErrors.email}
              aria-describedby={fieldErrors.email ? "reg-email-error" : undefined}
              className={`h-[44px] px-3 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors disabled:bg-[#F6F4EF] ${
                fieldErrors.email ? "border-[#B03028]" : "border-[#E3DFD8] focus:border-[#1C3558]"
              }`}
            />
            {fieldErrors.email && (
              <span id="reg-email-error" className="font-sans text-[12px] text-[#B03028] mt-[4px]">{fieldErrors.email}</span>
            )}
          </div>

          <div className="flex flex-col">
            <label htmlFor="reg-password" className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Password
            </label>
            <div className="relative">
              <input
                id="reg-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => { setPassword(e.target.value); if (errorMessage) setErrorMessage(""); }}
                disabled={isLoading}
                placeholder="Min. 8 characters"
                aria-invalid={!!fieldErrors.password}
                aria-describedby={fieldErrors.password ? "reg-password-error" : undefined}
                className={`w-full h-[44px] pl-3 pr-12 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors duration-fast ease-out disabled:bg-[#F6F4EF] ${!showPassword ? 'tracking-widest' : ''} ${
                  fieldErrors.password ? "border-[#B03028]" : "border-[#E3DFD8] focus:border-[#1C3558]"
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
            {fieldErrors.password && (
              <span id="reg-password-error" className="font-sans text-[12px] text-[#B03028] mt-[4px] tracking-normal transition-all duration-fast ease-out">{fieldErrors.password}</span>
            )}
          </div>

          <div className="flex flex-col">
            <label htmlFor="reg-confirm" className="font-sans text-[12px] font-semibold text-[#1A1A18] mb-[6px]">
              Confirm Password
            </label>
            <div className="relative">
              <input
                id="reg-confirm"
                type={showConfirm ? "text" : "password"}
                value={confirm}
                onChange={(e) => { setConfirm(e.target.value); if (errorMessage) setErrorMessage(""); }}
                disabled={isLoading}
                placeholder="Repeat password"
                aria-invalid={!!fieldErrors.confirm}
                aria-describedby={fieldErrors.confirm ? "reg-confirm-error" : undefined}
                className={`w-full h-[44px] pl-3 pr-12 font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] bg-[#FFFFFF] border rounded-[6px] outline-none transition-colors duration-fast ease-out disabled:bg-[#F6F4EF] ${!showConfirm ? 'tracking-widest' : ''} ${
                  fieldErrors.confirm ? "border-[#B03028]" : "border-[#E3DFD8] focus:border-[#1C3558]"
                }`}
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 font-sans text-[12px] text-[#1C3558] select-none hover:underline focus-visible:outline-none focus-visible:underline"
              >
                {showConfirm ? "Hide" : "Show"}
              </button>
            </div>
            {fieldErrors.confirm && (
              <span id="reg-confirm-error" className="font-sans text-[12px] text-[#B03028] mt-[4px] tracking-normal transition-all duration-fast ease-out">{fieldErrors.confirm}</span>
            )}
          </div>

          <div className="flex flex-col mt-2">
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="terms"
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  disabled={isLoading}
                  aria-describedby={fieldErrors.terms ? "reg-terms-error" : undefined}
                  className="w-4 h-4 bg-[#FFFFFF] border-[#E3DFD8] rounded-[4px] accent-[#1C3558] cursor-pointer disabled:cursor-not-allowed"
                />
              </div>
              <label htmlFor="terms" className="ml-3 font-sans text-[12px] text-[#7A786F] cursor-pointer">
                I agree to the <Link href="#" className="text-[#1C3558]">Terms of Service</Link> and <Link href="#" className="text-[#1C3558]">Privacy Policy</Link>.
              </label>
            </div>
            {fieldErrors.terms && (
              <span id="reg-terms-error" className="font-sans text-[12px] text-[#B03028] mt-[4px]">{fieldErrors.terms}</span>
            )}
          </div>

          {errorMessage && (
            <span role="alert" className="font-sans text-[12px] text-[#B03028]">{errorMessage}</span>
          )}

          <Button
            type="submit"
            variant="primary"
            className="w-full mt-2"
            isLoading={isLoading}
            loadingText="Creating account..."
          >
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
