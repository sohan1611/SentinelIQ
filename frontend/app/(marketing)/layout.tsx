import { Navbar } from "@/components/layout/Navbar"

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-border py-8 text-center text-sm text-secondary">
        <p>© {new Date().getFullYear()} SentinelIQ. Institutional Financial Forensics.</p>
      </footer>
    </div>
  )
}
