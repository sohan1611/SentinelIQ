"use client";

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { AppShell } from "@/components/layout/AppShell"
import { PageTransition } from "@/components/layout/PageTransition"
import { CommandPalette } from "@/components/layout/CommandPalette"
import { ToastProvider } from "@/contexts/ToastContext"
import { useAuth } from "@/contexts/AuthContext"
import { ROUTES } from "@/lib/constants/routes"

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const [isPaletteOpen, setIsPaletteOpen] = useState(false)

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace(ROUTES.login)
    }
  }, [isLoading, user, router])

  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        setIsPaletteOpen((v) => !v)
      }
    }
    window.addEventListener("keydown", handle)
    return () => window.removeEventListener("keydown", handle)
  }, [])

  if (isLoading || !user) {
    return <div className="min-h-screen bg-canvas" />
  }

  return (
    <ToastProvider>
      <AppShell>
        <PageTransition>{children}</PageTransition>
      </AppShell>
      <CommandPalette isOpen={isPaletteOpen} onClose={() => setIsPaletteOpen(false)} />
    </ToastProvider>
  )
}
