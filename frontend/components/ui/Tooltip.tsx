"use client";

import * as React from "react"

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}

const SIDE_STYLES: Record<NonNullable<TooltipProps["side"]>, string> = {
  top: "bottom-full left-1/2 -translate-x-1/2 mb-[6px]",
  bottom: "top-full left-1/2 -translate-x-1/2 mt-[6px]",
  left: "right-full top-1/2 -translate-y-1/2 mr-[6px]",
  right: "left-full top-1/2 -translate-y-1/2 ml-[6px]",
}

export function Tooltip({ content, children, side = "top", className = "" }: TooltipProps) {
  const [visible, setVisible] = React.useState(false)
  const showTimer = React.useRef<ReturnType<typeof setTimeout>>()

  const show = () => {
    showTimer.current = setTimeout(() => setVisible(true), 200)
  }
  const hide = () => {
    clearTimeout(showTimer.current)
    setVisible(false)
  }

  return (
    <span
      className={`relative inline-flex ${className}`}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      <span
        role="tooltip"
        className={`absolute z-50 whitespace-nowrap pointer-events-none px-2 py-1 rounded-[4px] bg-navy text-white font-sans text-xs leading-none ${SIDE_STYLES[side]}`}
        style={{
          opacity: visible ? 1 : 0,
          transition: "opacity var(--duration-fast) var(--ease-out)",
        }}
      >
        {content}
      </span>
    </span>
  )
}
