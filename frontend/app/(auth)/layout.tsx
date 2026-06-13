export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#F6F4EF] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-[400px]">
        {children}
      </div>
    </div>
  )
}
