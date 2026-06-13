"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import { Button } from "../ui/Button";

interface SearchBarProps {
  variant?: "hero" | "compact";
  forceState?: "default" | "focused" | "typed" | "loading";
  placeholder?: string;
}

export function SearchBar({ variant = "hero", forceState, placeholder }: SearchBarProps) {
  const isHero = variant === "hero";
  
  const [internalValue, setInternalValue] = useState(forceState === "typed" ? "Wirecard" : "");
  const [isFocused, setIsFocused] = useState(forceState === "focused" || forceState === "typed");
  const [isSubmitting, setIsSubmitting] = useState(forceState === "loading");

  const [dropdownActive, setDropdownActive] = useState(false);
  const [dropdownVisible, setDropdownVisible] = useState(false);

  const inputHeight = isHero ? "h-[52px] md:h-[56px]" : "h-[42px]";
  const defaultPlaceholder = isHero ? "Search a company or ticker — e.g. TSLA" : "Investigate a company...";
  const finalPlaceholder = placeholder || defaultPlaceholder;
  
  const shouldShowDropdown = isFocused && internalValue.length > 0;

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

  const focusStyles = isFocused ? "border-[#1C3558] ring-0" : "border-[#E3DFD8]";

  return (
    <div className={`relative w-full ${isHero ? "max-w-[640px] mx-auto" : "w-full"}`}>
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
          disabled={isSubmitting}
          className={`flex-1 w-full bg-transparent px-4 font-sans text-[14px] md:text-[15px] text-[#1A1A18] placeholder:text-[#B0ADA7] focus:outline-none h-full ${isSubmitting ? "cursor-not-allowed" : ""}`}
        />
        
        {isHero && (
          <div className="hidden md:block pr-2">
            <Button 
              variant="primary" 
              isLoading={isSubmitting} 
              className="h-[40px] px-6"
              onClick={() => setIsSubmitting(true)}
            >
              Search
            </Button>
          </div>
        )}
      </div>

      {isHero && (
        <div className="mt-3 md:hidden">
          <Button 
            variant="primary" 
            isLoading={isSubmitting} 
            className="w-full h-[44px]"
            onClick={() => setIsSubmitting(true)}
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
        </div>
      )}
    </div>
  );
}
