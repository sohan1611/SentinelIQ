"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

export type ToastType = "success" | "info" | "error";

interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const MAX_TOASTS = 3;
const AUTO_DISMISS_MS = 3000;

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "success") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }].slice(-MAX_TOASTS));
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

type ToastPhase = "enter" | "visible" | "exit";

const TOAST_ICONS: Record<ToastType, React.ReactNode> = {
  success: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M13.3334 4L6.00008 11.3333L2.66675 8" stroke="#1A6B3C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  info: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="8" cy="8" r="6.66667" stroke="#1C3558" strokeWidth="1.5" />
      <path d="M8 10.6667V8" stroke="#1C3558" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8" cy="5.33333" r="1" fill="#1C3558" />
    </svg>
  ),
  error: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="8" cy="8" r="6.66667" stroke="#B03028" strokeWidth="1.5" />
      <path d="M8 5.33333V8.66667" stroke="#B03028" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8" cy="10.6667" r="1" fill="#B03028" />
    </svg>
  ),
};

const TOAST_PHASE_STYLE: Record<ToastPhase, { opacity: number; transform: string; transition: string }> = {
  enter: {
    opacity: 0,
    transform: "translateX(16px)",
    transition: "none",
  },
  visible: {
    opacity: 1,
    transform: "translateX(0) translateY(0)",
    transition: "opacity var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out)",
  },
  exit: {
    opacity: 0,
    transform: "translateY(8px)",
    transition: "opacity var(--duration-fast) var(--ease-in), transform var(--duration-fast) var(--ease-in)",
  },
};

function ToastItem({ toast, onRemove }: { toast: ToastMessage; onRemove: (id: string) => void }) {
  const [phase, setPhase] = useState<ToastPhase>("enter");

  useEffect(() => {
    const raf = requestAnimationFrame(() => setPhase("visible"));
    const dismissTimer = setTimeout(() => setPhase("exit"), AUTO_DISMISS_MS);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(dismissTimer);
    };
  }, []);

  useEffect(() => {
    if (phase !== "exit") return;
    const removeTimer = setTimeout(() => onRemove(toast.id), 150);
    return () => clearTimeout(removeTimer);
  }, [phase, toast.id, onRemove]);

  const style = TOAST_PHASE_STYLE[phase];

  return (
    <div
      className="bg-surface border border-border rounded-card w-[320px] px-4 py-3 flex items-center"
      style={{
        opacity: style.opacity,
        transform: style.transform,
        transition: style.transition,
      }}
    >
      <div className="shrink-0 mr-3">{TOAST_ICONS[toast.type]}</div>
      <div className="font-sans text-sm font-medium text-text-primary">{toast.message}</div>
    </div>
  );
}
