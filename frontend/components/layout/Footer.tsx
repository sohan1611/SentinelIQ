import Link from "next/link"

export function Footer() {
  return (
    <footer className="w-full border-t border-border bg-canvas">
      <div className="mx-auto flex flex-col md:flex-row min-h-20 py-6 md:py-0 max-w-[1080px] items-center justify-between px-5 md:px-6 gap-4 md:gap-0">
        <div className="text-[11px] md:text-[12px] font-sans text-text-muted text-center md:text-left">
          © 2025 SentinelIQ. All rights reserved.
        </div>
        
        <nav className="flex flex-col md:flex-row items-center gap-2 md:gap-3 text-[11px] md:text-[12px] font-sans text-text-secondary">
          <div className="flex items-center gap-3">
            <Link href="#how-it-works" className="hover:text-text-primary transition-colors">How It Works</Link>
            <span className="text-border hidden md:inline">·</span>
            <Link href="#methodology" className="hover:text-text-primary transition-colors">Methodology</Link>
            <span className="text-border hidden md:inline">·</span>
            <Link href="#case-studies" className="hover:text-text-primary transition-colors">Case Studies</Link>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-border hidden md:inline">·</span>
            <Link href="/privacy" className="hover:text-text-primary transition-colors">Privacy</Link>
            <span className="text-border hidden md:inline">·</span>
            <Link href="/terms" className="hover:text-text-primary transition-colors">Terms</Link>
          </div>
        </nav>

        <div className="text-[11px] font-sans italic text-text-muted text-center md:text-right">
          Not investment advice. For research purposes only.
        </div>
      </div>
    </footer>
  )
}
