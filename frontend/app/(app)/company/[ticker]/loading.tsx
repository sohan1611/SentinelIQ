import { Skeleton } from "@/components/ui/Skeleton"

export default function OverviewLoading() {
  return (
    <div className="flex flex-col md:flex-row gap-8 mt-6">
      {/* Left Column - 35% */}
      <div className="w-full md:w-[35%] flex flex-col gap-6">
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6 flex flex-col items-center">
          <Skeleton className="w-[180px] h-[14px] mb-6" />
          <Skeleton className="w-[200px] h-[100px] rounded-t-full mb-8" />
          
          <div className="w-full h-[1px] bg-[#E3DFD8] mb-6" />
          <Skeleton className="w-[120px] h-[14px] mb-4" />
          
          <div className="flex flex-col gap-4 mb-6 w-full">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex flex-col gap-2">
                <div className="flex justify-between">
                  <Skeleton className="w-[100px] h-[12px]" />
                  <Skeleton className="w-[20px] h-[12px]" />
                </div>
                <Skeleton className="w-full h-[6px] rounded-full" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Column - 65% */}
      <div className="w-full md:w-[65%] flex flex-col gap-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-5 h-[140px]">
              <Skeleton className="w-1/2 h-[16px] mb-4" />
              <Skeleton className="w-[60px] h-[32px] mb-4" />
              <Skeleton className="w-full h-[14px]" />
            </div>
          ))}
        </div>
        
        <div className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] p-6">
          <Skeleton className="w-[150px] h-[14px] mb-6" />
          <div className="flex flex-col gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="w-2 h-2 rounded-full" />
                <Skeleton className="w-[60px] h-[12px]" />
                <Skeleton className="w-full h-[12px]" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
