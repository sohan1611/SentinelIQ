"use client";

import * as React from "react"
import { createPortal } from "react-dom"

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: "sm" | "md" | "lg";
}

const SIZES: Record<NonNullable<ModalProps["size"]>, string> = {
  sm: "max-w-[400px]",
  md: "max-w-[560px]",
  lg: "max-w-[760px]",
}

const FOCUSABLE =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function Modal({ isOpen, onClose, title, children, footer, size = "md" }: ModalProps) {
  const panelRef = React.useRef<HTMLDivElement>(null)
  const previousFocus = React.useRef<HTMLElement | null>(null)
  const titleId = React.useId()

  // Capture trigger element on open; restore focus on close
  React.useEffect(() => {
    if (isOpen) {
      previousFocus.current = document.activeElement as HTMLElement
    } else if (previousFocus.current) {
      previousFocus.current.focus?.()
      previousFocus.current = null
    }
  }, [isOpen])

  // Focus first interactive element when modal opens (close button or first input)
  React.useEffect(() => {
    if (!isOpen) return
    const frame = requestAnimationFrame(() => {
      const first = panelRef.current?.querySelector<HTMLElement>(FOCUSABLE)
      ;(first ?? panelRef.current)?.focus()
    })
    return () => cancelAnimationFrame(frame)
  }, [isOpen])

  // Escape + body scroll lock + Tab focus trap
  React.useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose()
        return
      }
      if (e.key !== "Tab") return

      const focusable = Array.from(
        panelRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? []
      )
      if (!focusable.length) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    document.body.style.overflow = "hidden"
    return () => {
      document.removeEventListener("keydown", handleKeyDown)
      document.body.style.overflow = ""
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{
        backgroundColor: "rgba(26, 26, 24, 0.4)",
        animation: "modal-overlay-in var(--duration-base) var(--ease-out)",
      }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        aria-label={!title ? "Dialog" : undefined}
        tabIndex={-1}
        className={`w-full ${SIZES[size]} bg-surface border border-border rounded-card max-h-[85vh] flex flex-col outline-none`}
        style={{ animation: "modal-panel-in var(--duration-base) var(--ease-out)" }}
      >
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-border shrink-0">
            <h2 id={titleId} className="font-sans text-lg font-semibold text-text-primary">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close dialog"
              className="font-sans text-[20px] leading-none text-text-secondary hover:text-text-primary transition-colors duration-instant"
            >
              ×
            </button>
          </div>
        )}
        <div className="px-6 py-5 overflow-y-auto font-sans text-base text-text-primary">
          {children}
        </div>
        {footer && (
          <div className="px-6 py-4 border-t border-border flex items-center justify-end gap-3 shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}
