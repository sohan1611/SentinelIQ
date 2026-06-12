import Link from "next/link"
import { Button } from "@/components/ui/Button"

export function Navbar() {
  return (
    <header className="w-full border-b border-border bg-canvas">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <Link href="/" className="text-xl font-serif font-semibold text-navy">
            SentinelIQ
          </Link>
        </div>
        <nav className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-secondary hover:text-primary transition-colors">
            Sign In
          </Link>
          <Link href="/dashboard">
            <Button variant="primary">Get Started</Button>
          </Link>
        </nav>
      </div>
    </header>
  )
}
