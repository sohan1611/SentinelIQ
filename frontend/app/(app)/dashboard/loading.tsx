import { Skeleton } from "@/components/ui/Skeleton"

export default function DashboardLoading() {
  return (
    <div className="w-full max-w-[1200px]">
      <div className="flex justify-between items-center mb-6">
        <h1 className="font-sans text-[22px] font-semibold text-[#1A1A18]">Dashboard</h1>
        <Skeleton className="w-[120px] h-[32px] rounded-btn" />
      </div>

      <div className="mb-[28px] w-full">
        <Skeleton className="w-full h-[42px] rounded-[6px]" />
      </div>

      <div className="mb-10">
        <div className="flex justify-between items-end mb-4">
          <Skeleton className="w-[80px] h-[14px]" />
          <Skeleton className="w-[100px] h-[16px]" />
        </div>

        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] overflow-hidden mb-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className={`flex items-center px-4 h-[52px] ${i !== 5 ? "border-b border-[#E3DFD8]" : ""}`}>
              <Skeleton className="w-[30%] h-[16px] mr-4" />
              <Skeleton className="w-[10%] h-[16px] mr-4" />
              <Skeleton className="w-[15%] h-[16px] mr-4" />
              <Skeleton className="w-[15%] h-[24px] rounded-full mr-4" />
              <Skeleton className="w-[15%] h-[16px] mr-4" />
              <Skeleton className="w-[15%] h-[16px]" />
            </div>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-4">
          <Skeleton className="w-[120px] h-[14px]" />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-5 h-[160px] flex flex-col justify-between">
              <div>
                <Skeleton className="w-3/4 h-[16px] mb-2" />
                <Skeleton className="w-1/4 h-[14px] mb-4" />
                <Skeleton className="w-1/2 h-[24px]" />
              </div>
              <Skeleton className="w-full h-[14px]" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
