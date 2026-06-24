"use client";

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import { useAlerts } from "@/lib/hooks/useAlerts"
import { ROUTES } from "@/lib/constants/routes"

const NAV_ITEMS_TOP = [
  { label: "Dashboard", href: "/dashboard" },
  { label: "Search", href: "/search" },
  { label: "Watchlist", href: "/watchlist" },
  { label: "Alerts", href: "/alerts" },
];

function getInitials(user: { full_name: string | null; email: string }): string {
  if (user.full_name) {
    const parts = user.full_name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  }
  return user.email.slice(0, 2).toUpperCase();
}

export function Sidebar() {
  const pathname = usePathname() || "/dashboard";
  const router = useRouter();
  const { user, logout } = useAuth();
  const { unreadCount } = useAlerts();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen hidden md:flex flex-col w-[180px] lg:w-[240px] border-r border-border bg-[#FFFFFF]">
      <div className="flex h-[72px] items-center px-5 pt-6 pb-4">
        <Link href="/dashboard" className="text-[15px] font-sans font-semibold text-text-primary">
          SentinelIQ
        </Link>
      </div>
      
      <div className="w-full h-[1px] bg-border mb-4" />
      
      <nav className="flex flex-col flex-1">
        <div className="flex flex-col">
          {NAV_ITEMS_TOP.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/") && item.href !== "/";
            const label = item.href === "/alerts" && unreadCount > 0 ? `${item.label} (${unreadCount})` : item.label;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center px-5 py-[10px] font-sans text-[14px] ${
                  isActive
                    ? "border-l-2 border-navy text-text-primary font-semibold bg-transparent"
                    : "border-l-2 border-transparent text-text-secondary hover:bg-[#F6F4EF] font-normal transition-colors duration-instant ease-out"
                }`}
              >
                {label}
              </Link>
            )
          })}
        </div>
        
        <div className="w-full h-[1px] bg-border my-4" />
        
        <Link
          href="/settings"
          className={`flex items-center px-5 py-[10px] font-sans text-[14px] ${
            pathname.startsWith("/settings")
              ? "border-l-2 border-navy text-text-primary font-semibold bg-transparent" 
              : "border-l-2 border-transparent text-text-secondary hover:bg-[#F6F4EF] font-normal transition-colors duration-instant ease-out"
          }`}
        >
          Settings
        </Link>
        
        <div className="mt-auto pb-6 px-5 flex flex-col items-start">
          <div className="flex items-center gap-3 mb-2 w-full">
            <div className="w-[32px] h-[32px] rounded-full bg-border flex items-center justify-center text-[12px] font-sans font-medium text-text-secondary shrink-0">
              {user ? getInitials(user) : ""}
            </div>
            <div className="font-sans text-[12px] text-text-secondary truncate pr-2">
              {user?.email ?? ""}
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              router.push(ROUTES.login);
            }}
            className="font-sans text-[12px] text-text-muted hover:text-text-primary transition-colors duration-instant text-left pl-[44px]"
          >
            Sign Out
          </button>
        </div>
      </nav>
    </aside>
  )
}
