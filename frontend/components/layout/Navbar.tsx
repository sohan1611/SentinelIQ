import Link from "next/link"
import { Button } from "@/components/ui/Button"

export function Navbar() {
  return (
    <header className="w-full bg-canvas">
      <div className="mx-auto flex h-20 max-w-[1080px] items-center justify-between px-5 md:px-6">
        <div className="flex items-center gap-2">
          <Link href="/" className="text-[15px] font-sans font-semibold text-text-primary">
            SentinelIQ
          </Link>
        </div>
        <nav className="flex items-center gap-6">
          <Link href="#how-it-works" className="hidden md:block text-[14px] font-sans text-text-secondary hover:text-text-primary transition-colors">
            How It Works
          </Link>
          <Link href="#methodology" className="hidden md:block text-[14px] font-sans text-text-secondary hover:text-text-primary transition-colors">
            Methodology
          </Link>
          <Link href="#case-studies" className="hidden md:block text-[14px] font-sans text-text-secondary hover:text-text-primary transition-colors">
            Case Studies
          </Link>
          <Link href="/login" className="hidden md:block text-[14px] font-sans text-navy hover:text-[#142848] transition-colors ml-2">
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
