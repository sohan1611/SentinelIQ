"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [displayChildren, setDisplayChildren] = useState(children);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    if (pathname) {
      // Start outgoing transition
      setIsTransitioning(true);
      
      const timer = setTimeout(() => {
        // Swap content while opacity is 0
        setDisplayChildren(children);
        // Start incoming transition
        setIsTransitioning(false);
      }, 100); // Wait for 100ms outgoing fade

      return () => clearTimeout(timer);
    }
  }, [pathname, children]);

  return (
    <div
      className="w-full h-full"
      style={{
        opacity: isTransitioning ? 0 : 1,
        transition: isTransitioning 
          ? "opacity 100ms var(--ease-in)" 
          : "opacity 200ms var(--ease-out)"
      }}
    >
      {displayChildren}
    </div>
  );
}
