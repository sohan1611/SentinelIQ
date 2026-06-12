import { Sidebar } from "./Sidebar"
import { BottomTabBar } from "./BottomTabBar"

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-canvas">
      <Sidebar />
      <main className="pb-[72px] md:pb-0 md:pl-[180px] lg:pl-[240px]">
        <div className="px-5 py-6 md:px-[40px] md:py-[32px]">
          {children}
        </div>
      </main>
      <BottomTabBar />
    </div>
  )
}
