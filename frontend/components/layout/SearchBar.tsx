import * as React from "react";
import { Button } from "../ui/Button";

interface SearchBarProps {
  variant?: "hero" | "compact";
  forceState?: "default" | "focused" | "typed" | "loading";
  placeholder?: string;
}

export function SearchBar({ variant = "hero", forceState, placeholder }: SearchBarProps) {
  const isHero = variant === "hero";
  
  // Base input styles
  const inputHeight = isHero ? "h-[52px] md:h-[56px]" : "h-[42px]";
  const defaultPlaceholder = isHero ? "Search a company or ticker — e.g. TSLA" : "Investigate a company...";
  const finalPlaceholder = placeholder || defaultPlaceholder;
  
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
          placeholder={finalPlaceholder}
          defaultValue={hasInput ? "Wirecard" : ""}
          className="flex-1 w-full bg-transparent px-4 font-sans text-[14px] md:text-[15px] text-text-primary placeholder:text-text-muted focus:outline-none h-full"
          readOnly={!!forceState} 
        />
        
        {isHero && (
          <div className="hidden md:block pr-2">
            <Button variant="primary" isLoading={isLoading} className="h-[40px] px-6">
              Search
            </Button>
          </div>
        )}
      </div>

      {isHero && (
        <div className="mt-3 md:hidden">
          <Button variant="primary" isLoading={isLoading} className="w-full h-[44px]">
            Search
          </Button>
        </div>
      )}

      {/* Dropdown Suggestion Box */}
      {hasInput && (
        <div className={`absolute left-0 w-full bg-surface border border-border rounded-[8px] z-50 overflow-hidden shadow-sm ${isHero ? "top-[calc(100%-48px)] md:top-[calc(100%+8px)]" : "top-[calc(100%+8px)]"}`}>
          <div className="flex justify-between items-center px-4 py-3 min-h-[48px] border-b border-border hover:bg-[#F1EFE9] cursor-pointer">
            <span className="font-sans text-[14px] font-semibold text-text-primary">Wirecard AG</span>
            <span className="font-mono text-[12px] text-navy">WDI.DE</span>
          </div>
          <div className="flex justify-between items-center px-4 py-3 min-h-[48px] border-b border-border hover:bg-[#F1EFE9] cursor-pointer bg-[#F1EFE9]">
            <span className="font-sans text-[14px] font-semibold text-text-primary">Wirecard Card Solutions</span>
            <span className="font-mono text-[12px] text-navy">WDICS</span>
          </div>
          <div className="flex justify-between items-center px-4 py-3 min-h-[48px] hover:bg-[#F1EFE9] cursor-pointer">
            <span className="font-sans text-[14px] font-semibold text-text-primary">Wire Technologies</span>
            <span className="font-mono text-[12px] text-navy">WIRE</span>
          </div>
        </div>
      )}
    </div>
  );
}
