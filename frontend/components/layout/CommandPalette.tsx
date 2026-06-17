"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { searchCompanies } from "@/lib/api/company";
import { useDebounce } from "@/lib/hooks/useDebounce";
import type { Company } from "@/types/company";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Search companies", href: "/search" },
  { label: "Watchlist", href: "/watchlist" },
  { label: "Settings", href: "/settings" },
];

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Company[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const debouncedQuery = useDebounce(query, 220);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setResults([]);
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 10);
    }
  }, [isOpen]);

  // Fetch search results
  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults([]);
      setActiveIndex(0);
      return;
    }
    let cancelled = false;
    setIsSearching(true);
    searchCompanies(debouncedQuery)
      .then((r) => {
        if (!cancelled) {
          setResults(r);
          setActiveIndex(0);
        }
      })
      .catch(() => {
        if (!cancelled) setResults([]);
      })
      .finally(() => {
        if (!cancelled) setIsSearching(false);
      });
    return () => { cancelled = true; };
  }, [debouncedQuery]);

  const items = query.trim()
    ? results.map((c) => ({ label: c.name, sub: c.ticker, href: `/company/${c.ticker}` }))
    : NAV_ITEMS.map((n) => ({ label: n.label, sub: undefined, href: n.href }));

  const navigate = useCallback((href: string) => {
    onClose();
    router.push(href);
  }, [router, onClose]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;
    const handle = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, items.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter" && items[activeIndex]) {
        navigate(items[activeIndex].href);
      }
    };
    window.addEventListener("keydown", handle);
    return () => window.removeEventListener("keydown", handle);
  }, [isOpen, items, activeIndex, navigate, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-[#1A1A18]/20" />

      {/* Palette card */}
      <div
        className="relative w-full max-w-[560px] mx-4 bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden"
        style={{
          animation: "paletteIn 150ms cubic-bezier(0.0, 0.0, 0.2, 1.0) both",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center border-b border-[#E3DFD8] px-4 h-[52px] gap-3">
          <span className="font-sans text-[13px] text-[#B0ADA7] shrink-0">Search</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Company name or ticker..."
            className="flex-1 bg-transparent font-sans text-[14px] text-[#1A1A18] placeholder:text-[#B0ADA7] outline-none"
          />
          {isSearching && (
            <span className="font-sans text-[11px] text-[#B0ADA7] shrink-0">...</span>
          )}
          <kbd className="font-mono text-[10px] text-[#B0ADA7] border border-[#E3DFD8] rounded px-1.5 py-0.5 shrink-0">Esc</kbd>
        </div>

        {/* Results / Nav items */}
        {items.length > 0 && (
          <ul className="py-1 max-h-[320px] overflow-y-auto">
            {query.trim() && (
              <li className="px-4 py-2">
                <span className="font-sans text-[10px] font-medium uppercase tracking-[0.07em] text-[#B0ADA7]">
                  Companies
                </span>
              </li>
            )}
            {!query.trim() && (
              <li className="px-4 py-2">
                <span className="font-sans text-[10px] font-medium uppercase tracking-[0.07em] text-[#B0ADA7]">
                  Navigation
                </span>
              </li>
            )}
            {items.map((item, i) => (
              <li key={item.href}>
                <button
                  className={`w-full flex items-center justify-between px-4 py-2.5 text-left transition-colors ${
                    i === activeIndex ? "bg-[#F6F4EF]" : "hover:bg-[#F6F4EF]"
                  }`}
                  onMouseEnter={() => setActiveIndex(i)}
                  onClick={() => navigate(item.href)}
                >
                  <span className="font-sans text-[14px] text-[#1A1A18]">{item.label}</span>
                  {item.sub && (
                    <span className="font-mono text-[12px] text-[#1C3558]">{item.sub}</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}

        {query.trim() && !isSearching && results.length === 0 && (
          <div className="px-4 py-6 text-center">
            <span className="font-sans text-[13px] text-[#B0ADA7]">
              No companies found for &ldquo;{query}&rdquo;
            </span>
          </div>
        )}
      </div>

      <style>{`
        @keyframes paletteIn {
          from { opacity: 0; transform: translateY(-8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
