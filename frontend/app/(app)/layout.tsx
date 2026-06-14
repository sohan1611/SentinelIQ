"use client";

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { AppShell } from "@/components/layout/AppShell"
import { PageTransition } from "@/components/layout/PageTransition"
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

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace(ROUTES.login)
    }
  }, [isLoading, user, router])

  if (isLoading || !user) {
    return <div className="min-h-screen bg-canvas" />
  }

  return (
    <ToastProvider>
      <AppShell>
        <PageTransition>{children}</PageTransition>
      </AppShell>
    </ToastProvider>
  )
}
