import * as React from "react"
import { Skeleton } from "./Skeleton"

export interface DataTableColumn<T> {
  key: string;
  header: string;
  width?: string;
  align?: "left" | "right" | "center";
  className?: string;
  render?: (row: T, index: number) => React.ReactNode;
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  getRowKey: (row: T, index: number) => string | number;
  onRowClick?: (row: T) => void;
  isLoading?: boolean;
  skeletonRows?: number;
  emptyState?: React.ReactNode;
  className?: string;
  ariaLabel?: string;
}

const ALIGN_CLASS: Record<NonNullable<DataTableColumn<unknown>["align"]>, string> = {
  left: "text-left",
  right: "text-right",
  center: "text-center",
}

export function DataTable<T>({
  columns,
  data,
  getRowKey,
  onRowClick,
  isLoading = false,
  skeletonRows = 5,
  emptyState,
  className = "",
  ariaLabel,
}: DataTableProps<T>) {
  return (
    <div className={`bg-surface border border-border rounded-card overflow-hidden ${className}`}>
      <table aria-label={ariaLabel} className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                style={{ width: col.width }}
                className={`py-3 px-4 font-sans text-2xs font-medium uppercase tracking-[0.08em] text-text-secondary ${ALIGN_CLASS[col.align ?? "left"]}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            [...Array(skeletonRows)].map((_, i) => (
              <tr key={i} className={i !== skeletonRows - 1 ? "border-b border-border" : ""}>
                {columns.map((col) => (
                  <td key={col.key} className="h-[52px] px-4">
                    <Skeleton className="h-[16px] w-3/4" />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="py-12 px-4 text-center">
                {emptyState ?? (
                  <span className="font-sans text-base text-text-secondary">No data available.</span>
                )}
              </td>
            </tr>
          ) : (
            data.map((row, i) => (
              <tr
                key={getRowKey(row, i)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`h-[52px] ${onRowClick ? "cursor-pointer hover:bg-[#F1EFE9]" : ""} ${i !== data.length - 1 ? "border-b border-border" : ""}`}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-4 text-base ${ALIGN_CLASS[col.align ?? "left"]} ${col.className ?? ""}`}
                  >
                    {col.render ? col.render(row, i) : String((row as Record<string, unknown>)[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
