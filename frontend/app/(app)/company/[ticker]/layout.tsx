"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function CompanyLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { ticker: string };
}) {
  const ticker = params.ticker || "WDI.DE";
  const pathname = usePathname();

  // If we are on the report page, we don't show the standard header and tabs
  // Actually, the prompt says for Report Page: "Shell: Same sidebar. Sub-navigation tabs shown (Report is active)... PAGE HEADER: Label: AI FORENSIC REPORT"
  // Wait, "This page is intentionally different from the tab screens... PAGE HEADER: AI FORENSIC REPORT". It implies the sub-nav tabs are shown, but the page header is DIFFERENT.
  // "Sub-navigation tabs shown (Report is active). Content: Single centered column... PAGE HEADER: Label: AI FORENSIC REPORT"
  // This means the SubNavigation is ABOVE the page header on the report page, or maybe the Report page has its own header.
  // I will just put the Header and SubNav in the layout, but conditionally render the Header based on if it's the Report page?
  // Let's check the spec: "SUB-NAVIGATION (below app shell top, above content): Horizontal tab bar... Tab bar sits flush below the page header block."
  // And for Report Page: "Shell: Same sidebar. Sub-navigation tabs shown (Report is active). Content: Single centered column... PAGE HEADER: Label: AI FORENSIC REPORT"
  // So for the Report page, does it have the standard "Wirecard AG" header AND the "AI FORENSIC REPORT" header? Probably not. It says "PAGE HEADER: Label: AI FORENSIC REPORT". I will just render the tabs in a separate component and include them in the pages, or conditional rendering in layout.

  const isReport = pathname.includes("/report");

  const tabs = [
    { label: "Overview", href: `/company/${ticker}` },
    { label: "Financials", href: `/company/${ticker}/financials` },
    { label: "Governance", href: `/company/${ticker}/governance` },
    { label: "Narrative", href: `/company/${ticker}/narrative` },
    { label: "Report", href: `/company/${ticker}/report` },
  ];

  return (
    <div className="w-full max-w-[1200px]">
      {!isReport && (
        <div className="mb-0">
          <div className="flex justify-between items-end pb-6">
            <div>
              <h1 className="font-sans text-[26px] font-semibold text-[#1A1A18] mb-2">Wirecard AG</h1>
              <div className="flex items-center gap-2 font-sans text-[13px] text-[#7A786F]">
                <span className="font-mono text-[#1C3558]">{ticker === "WDI.DE" ? "WDI.DE" : ticker}</span>
                <span className="text-[#E3DFD8]">·</span>
                <span>Financial Technology</span>
                <span className="text-[#E3DFD8]">·</span>
                <span>Frankfurt Stock Exchange</span>
              </div>
            </div>
            <div className="font-sans text-[12px] text-[#B0ADA7]">
              Last analyzed: June 9, 2025
            </div>
          </div>
        </div>
      )}

      {/* Sub-navigation */}
      <div className={`w-full flex items-center border-b border-[#E3DFD8] bg-[#FFFFFF] ${isReport ? 'mb-8' : 'mb-8'} px-2 pt-2 rounded-t-[8px]`}>
        {tabs.map((tab) => {
          const isActive = tab.href === `/company/${ticker}` 
            ? pathname === `/company/${ticker}` 
            : pathname.startsWith(tab.href);

          return (
            <Link
              key={tab.label}
              href={tab.label === "Overview" ? `/company/${ticker}` : tab.href}
              className={`px-4 py-3 font-sans text-[14px] ${
                isActive
                  ? "font-semibold text-[#1A1A18] border-b-2 border-[#1C3558]"
                  : "text-[#7A786F] border-b-2 border-transparent hover:text-[#1A1A18]"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>

      <div className="w-full">
        {children}
      </div>
    </div>
  );
}
