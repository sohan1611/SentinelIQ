import * as React from "react"

export interface ChartFrameProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  height?: number | string;
  className?: string;
}

export function ChartFrame({ title, subtitle, actions, children, height = 280, className = "" }: ChartFrameProps) {
  return (
    <div className={`bg-surface border border-border rounded-card p-5 flex flex-col ${className}`}>
      <div className="flex items-start justify-between mb-4 gap-4">
        <div>
          <h3 className="font-sans text-2xs font-medium uppercase tracking-[0.08em] text-text-secondary">
            {title}
          </h3>
          {subtitle && <p className="font-sans text-sm text-text-muted mt-1">{subtitle}</p>}
        </div>
        {actions && <div className="shrink-0">{actions}</div>}
      </div>
      <div style={{ height }} className="relative w-full">
        {children}
      </div>
    </div>
  )
}
