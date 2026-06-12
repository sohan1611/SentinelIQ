import { Skeleton } from "@/components/ui/Skeleton"

export default function ReportLoading() {
  return (
    <div className="w-full flex justify-center mt-8 pb-16">
      <div className="w-full max-w-[760px] flex flex-col">
        
        {/* PAGE HEADER */}
        <div className="mb-8">
          <Skeleton className="w-[140px] h-[14px] mb-4" />
          <Skeleton className="w-[200px] h-[28px] mb-4" />
          <Skeleton className="w-[300px] h-[14px] mb-4" />
          <Skeleton className="w-[100px] h-[24px]" />
        </div>

        <div className="w-full h-[1px] bg-[#E3DFD8] mb-8" />

        {/* REPORT BODY SECTIONS */}
        <div className="flex flex-col gap-10">
          {[...Array(4)].map((_, i) => (
            <section key={i}>
              <Skeleton className="w-[120px] h-[12px] mb-2" />
              <Skeleton className="w-[200px] h-[20px] mb-4" />
              <div className="flex flex-col gap-2">
                <Skeleton className="w-full h-[16px]" />
                <Skeleton className="w-[90%] h-[16px]" />
                <Skeleton className="w-[95%] h-[16px]" />
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}
