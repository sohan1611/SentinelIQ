import * as React from "react"

export interface ChartFrameAccessibleSeries {
  label: string;
  values: (number | null)[];
  formatValue: (value: number) => string;
}

export interface ChartFrameAccessibleTable {
  labels: string[];
  series: ChartFrameAccessibleSeries[];
}

export interface ChartFrameProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  height?: number | string;
  className?: string;
  accessibleTable?: ChartFrameAccessibleTable;
}

export function ChartFrame({ title, subtitle, actions, children, height = 280, className = "", accessibleTable }: ChartFrameProps) {
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
      <div style={{ height }} className="relative w-full" aria-hidden={accessibleTable ? true : undefined}>
        {children}
      </div>
      {accessibleTable && (
        <table className="sr-only">
          <caption>{title}{subtitle ? ` — ${subtitle}` : ""}</caption>
          <thead>
            <tr>
              <th scope="col">Period</th>
              {accessibleTable.series.map((s) => (
                <th scope="col" key={s.label}>{s.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {accessibleTable.labels.map((label, i) => (
              <tr key={label}>
                <th scope="row">{label}</th>
                {accessibleTable.series.map((s) => {
                  const value = s.values[i]
                  return (
                    <td key={s.label}>{value == null ? "No data" : s.formatValue(value)}</td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
