import Link from "next/link"

const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Search", href: "/search" },
  { label: "Watchlist", href: "/watchlist" },
  { label: "Recent Reports", href: "/reports" },
  { label: "Settings", href: "/settings" },
];

export function Sidebar() {
  // Hardcoding active state to dashboard for now
  const pathname = "/dashboard"; 

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-[240px] border-r border-border bg-canvas">
      <div className="flex h-16 items-center px-6 mb-4">
        <Link href="/" className="text-xl font-serif font-semibold text-navy">
          SentinelIQ
        </Link>
      </div>
      <nav className="flex flex-col gap-1 px-3">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center px-3 py-2 text-sm font-medium transition-colors ${
                isActive 
                  ? "border-l-2 border-navy text-primary bg-surface/50" 
                  : "border-l-2 border-transparent text-secondary hover:text-primary hover:bg-surface/50"
              }`}
            >
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
