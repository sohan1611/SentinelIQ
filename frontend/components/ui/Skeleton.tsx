import * as React from "react"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`animate-[pulse_1.2s_ease-in-out_infinite] bg-skeleton rounded-[4px] ${className}`}
      {...props}
    />
  )
}

export { Skeleton }
