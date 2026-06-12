import * as React from "react";
import { Button } from "../ui/Button";

interface SearchBarProps {
  variant?: "hero" | "compact";
  forceState?: "default" | "focused" | "typed" | "loading";
}

export function SearchBar({ variant = "hero", forceState }: SearchBarProps) {
  const isHero = variant === "hero";
  
  // Base input styles
  const inputHeight = isHero ? "h-[56px]" : "h-[42px]";
  const placeholder = isHero ? "Search a company or ticker — e.g. TSLA" : "Investigate a company...";
  
  // State mapping for visual demonstration purposes
  const isFocused = forceState === "focused";
  const hasInput = forceState === "typed";
  const isLoading = forceState === "loading";
  
  const focusStyles = isFocused ? "border-navy ring-0" : "border-border";

  return (
    <div className={`relative w-full ${isHero ? "max-w-[640px] mx-auto" : "w-full"}`}>
      <div className={`flex items-center w-full bg-surface border ${focusStyles} rounded-[6px] transition-colors overflow-hidden ${inputHeight}`}>
        <input 
          type="text"
          placeholder={placeholder}
          defaultValue={hasInput ? "Wirecard" : ""}
          className="flex-1 bg-transparent px-4 font-sans text-[15px] text-text-primary placeholder:text-text-muted focus:outline-none h-full"
          readOnly={!!forceState} // Prevent actual typing to maintain forced states for the spec sheet
        />
        
        {isHero && (
          <div className="pr-2">
            <Button variant="primary" isLoading={isLoading} className="h-[40px] px-6">
              Search
            </Button>
          </div>
        )}
      </div>

      {/* Dropdown Suggestion Box */}
      {hasInput && (
        <div className="absolute top-[calc(100%+8px)] left-0 w-full bg-surface border border-border rounded-[8px] z-50 overflow-hidden shadow-sm">
          <div className="flex justify-between items-center px-4 py-3 border-b border-border hover:bg-[#F1EFE9] cursor-pointer">
            <span className="font-sans text-[14px] font-semibold text-text-primary">Wirecard AG</span>
            <span className="font-mono text-[12px] text-navy">WDI.DE</span>
          </div>
          <div className="flex justify-between items-center px-4 py-3 border-b border-border hover:bg-[#F1EFE9] cursor-pointer bg-[#F1EFE9]">
            <span className="font-sans text-[14px] font-semibold text-text-primary">Wirecard Card Solutions</span>
            <span className="font-mono text-[12px] text-navy">WDICS</span>
          </div>
          <div className="flex justify-between items-center px-4 py-3 hover:bg-[#F1EFE9] cursor-pointer">
            <span className="font-sans text-[14px] font-semibold text-text-primary">Wire Technologies</span>
            <span className="font-mono text-[12px] text-navy">WIRE</span>
          </div>
        </div>
      )}
    </div>
  );
}
