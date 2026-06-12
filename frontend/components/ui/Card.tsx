import * as React from "react"

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className = "", ...props }, ref) => (
  <div
    ref={ref}
    className={`rounded-card border border-border bg-surface text-primary ${className}`}
    {...props}
  />
))
Card.displayName = "Card"

export { Card }
