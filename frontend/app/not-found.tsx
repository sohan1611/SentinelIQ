import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#F6F4EF] flex flex-col items-center justify-center p-4">
      <div className="flex flex-col items-center justify-center text-center w-full max-w-[400px]">
        
        <div className="font-sans text-[16px] font-semibold text-[#1A1A18] mb-12">
          SentinelIQ
        </div>

        <div className="font-mono text-[96px] font-bold text-[#E3DFD8] leading-none mb-6">
          404
        </div>

        <h1 className="font-sans text-[20px] font-semibold text-[#1A1A18] mb-4">
          Page not found.
        </h1>

        <p className="font-sans text-[14px] text-[#7A786F] max-w-[360px] mx-auto mb-8 leading-[1.6]">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="flex items-center justify-center gap-4">
          <Link href="/dashboard">
            <Button variant="primary">Go to Dashboard</Button>
          </Link>
          <Link href="javascript:history.back()" className="font-sans text-[14px] text-[#7A786F] hover:text-[#1A1A18] transition-colors">
            Back
          </Link>
        </div>

      </div>
    </div>
  );
}
