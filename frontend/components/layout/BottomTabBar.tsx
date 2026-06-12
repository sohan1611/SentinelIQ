import Link from "next/link";

const NAV_ITEMS = [
  { label: "Home", href: "/dashboard" },
  { label: "Search", href: "/search" },
  { label: "Watchlist", href: "/watchlist" },
  { label: "Reports", href: "/reports" },
  { label: "Settings", href: "/settings" },
];

export function BottomTabBar() {
  // Hardcoded active state for demonstration
  const pathname = "/dashboard"; 

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-[56px] w-full bg-surface border-t border-border md:hidden">
      {NAV_ITEMS.map((item) => {
        const isActive = pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className="flex-1 flex flex-col items-center justify-center relative touch-manipulation"
          >
            {isActive && (
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-navy" />
            )}
            <span className={`font-sans text-[11px] ${isActive ? "font-semibold text-navy" : "font-normal text-text-muted"}`}>
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
