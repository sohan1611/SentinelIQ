"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "../ui/Button";
import { useDebounce } from "@/lib/hooks/useDebounce";
import { searchCompanies } from "@/lib/api/company";
import type { Company } from "@/types/company";

interface SearchBarProps {
  variant?: "hero" | "compact";
  // forceState drives static visual states for the design-system showcase only.
  forceState?: "default" | "focused" | "typed" | "loading";
  placeholder?: string;
  initialValue?: string;
}

export function SearchBar({ variant = "hero", forceState, placeholder, initialValue }: SearchBarProps) {
  const router = useRouter();
  const isHero = variant === "hero";
  const isDemo = forceState !== undefined;

  const [internalValue, setInternalValue] = useState(
    initialValue ?? (forceState === "typed" ? "Wirecard" : "")
  );
  const [isFocused, setIsFocused] = useState(forceState === "focused" || forceState === "typed");
  const [isSubmitting, setIsSubmitting] = useState(forceState === "loading");

  const [results, setResults] = useState<Company[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const [dropdownActive, setDropdownActive] = useState(false);
  const [dropdownVisible, setDropdownVisible] = useState(false);

  const debouncedValue = useDebounce(internalValue, 250);

  const inputHeight = isHero ? "h-[52px] md:h-[56px]" : "h-[42px]";
  const defaultPlaceholder = isHero ? "Search a company or ticker — e.g. TSLA" : "Investigate a company...";
  const finalPlaceholder = placeholder || defaultPlaceholder;

  const trimmed = internalValue.trim();
  const shouldShowDropdown = isFocused && trimmed.length > 0;

  // Live search against the backend (skipped in design-system demo mode).
  useEffect(() => {
    if (isDemo) return;
    const q = debouncedValue.trim();
    if (q.length === 0) {
      setResults([]);
      setIsSearching(false);
      return;
    }
    let cancelled = false;
    setIsSearching(true);
    searchCompanies(q)
      .then((data) => {
        if (!cancelled) setResults(data);
      })
      .catch(() => {
        if (!cancelled) setResults([]);
      })
      .finally(() => {
        if (!cancelled) setIsSearching(false);
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedValue, isDemo]);

  useEffect(() => {
    if (shouldShowDropdown) {
      setDropdownActive(true);
      // slight delay to allow display block to apply before transition
      requestAnimationFrame(() => setDropdownVisible(true));
    } else {
      setDropdownVisible(false);
      const timer = setTimeout(() => setDropdownActive(false), 100); // Wait for exit animation
      return () => clearTimeout(timer);
    }
  }, [shouldShowDropdown]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isDemo) {
      setIsSubmitting(true);
      return;
    }
    if (trimmed.length === 0) return;
    setIsSubmitting(true);
    router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  };

  const focusStyles = isFocused ? "border-[#1C3558] ring-0" : "border-[#E3DFD8]";

  return (
    <form onSubmit={handleSubmit} className={`relative w-full ${isHero ? "max-w-[640px] mx-auto" : "w-full"}`}>
      <div
        className={`flex items-center w-full bg-[#FFFFFF] border ${focusStyles} rounded-[6px] transition-colors var(--duration-fast) var(--ease-out) overflow-hidden ${inputHeight} ${isSubmitting ? "bg-[#F6F4EF]" : ""}`}
      >
        <input
          type="text"
          placeholder={finalPlaceholder}
          value={internalValue}
          onChange={(e) => setInternalValue(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          disabled={isDemo && isSubmitting}
          className={`flex-1 w-full bg-transparent px-4 font-sans text-[14px] md:text-[15px] text-[#1A1A18] placeholder:text-[#B0ADA7] focus:outline-none h-full ${isDemo && isSubmitting ? "cursor-not-allowed" : ""}`}
        />

        {isHero && (
          <div className="hidden md:block pr-2">
            <Button
              type="submit"
              variant="primary"
              isLoading={isSubmitting}
              className="h-[40px] px-6"
            >
              Search
            </Button>
          </div>
        )}
      </div>

      {isHero && (
        <div className="mt-3 md:hidden">
          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            className="w-full h-[44px]"
          >
            Search
          </Button>
        </div>
      )}

      {/* Dropdown Suggestion Box */}
      {dropdownActive && (
        <div
          className={`absolute left-0 w-full bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] z-50 overflow-hidden shadow-sm ${isHero ? "top-[calc(100%-48px)] md:top-[calc(100%+8px)]" : "top-[calc(100%+8px)]"}`}
          style={{
            opacity: dropdownVisible ? 1 : 0,
            transform: dropdownVisible ? "translateY(0)" : "translateY(-8px)",
            transition: dropdownVisible
              ? "opacity var(--duration-fast) var(--ease-out), transform var(--duration-fast) var(--ease-out)"
              : "opacity 100ms var(--ease-in), transform 100ms var(--ease-in)"
          }}
        >
          {isDemo ? (
            <>
              <div className="flex justify-between items-center px-4 py-3 min-h-[48px] border-b border-[#E3DFD8] hover:bg-[#F1EFE9] transition-colors var(--duration-instant) var(--ease-out) cursor-pointer">
                <span className="font-sans text-[14px] font-semibold text-[#1A1A18]">Wirecard AG</span>
                <span className="font-mono text-[12px] text-[#1C3558]">WDI.DE</span>
              </div>
              <div className="flex justify-between items-center px-4 py-3 min-h-[48px] border-b border-[#E3DFD8] hover:bg-[#F1EFE9] transition-colors var(--duration-instant) var(--ease-out) cursor-pointer">
                <span className="font-sans text-[14px] font-semibold text-[#1A1A18]">Wirecard Card Solutions</span>
                <span className="font-mono text-[12px] text-[#1C3558]">WDICS</span>
              </div>
              <div className="flex justify-between items-center px-4 py-3 min-h-[48px] hover:bg-[#F1EFE9] transition-colors var(--duration-instant) var(--ease-out) cursor-pointer">
                <span className="font-sans text-[14px] font-semibold text-[#1A1A18]">Wire Technologies</span>
                <span className="font-mono text-[12px] text-[#1C3558]">WIRE</span>
              </div>
            </>
          ) : results.length > 0 ? (
            results.map((c) => (
              <Link
                key={c.id}
                href={`/company/${c.ticker}`}
                className="flex justify-between items-center px-4 py-3 min-h-[48px] border-b border-[#E3DFD8] last:border-b-0 hover:bg-[#F1EFE9] transition-colors var(--duration-instant) var(--ease-out) cursor-pointer"
              >
                <span className="font-sans text-[14px] font-semibold text-[#1A1A18] truncate pr-3">{c.name}</span>
                <span className="font-mono text-[12px] text-[#1C3558] shrink-0">{c.ticker}</span>
              </Link>
            ))
          ) : (
            <div className="flex items-center px-4 py-3 min-h-[48px] font-sans text-[13px] text-[#7A786F]">
              {isSearching ? "Searching…" : "No matches — press Enter to search."}
            </div>
          )}
        </div>
      )}
    </form>
  );
}
