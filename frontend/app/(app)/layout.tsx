import { AppShell } from "@/components/layout/AppShell"
import { PageTransition } from "@/components/layout/PageTransition"
import { ToastProvider } from "@/contexts/ToastContext"

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ToastProvider>
      <AppShell>
        <PageTransition>{children}</PageTransition>
      </AppShell>
    </ToastProvider>
  )
}
