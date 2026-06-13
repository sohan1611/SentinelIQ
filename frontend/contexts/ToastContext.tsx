"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

export type ToastType = "success" | "info";

interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

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
    setToasts((prev) => [...prev, { id, message, type }]);
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

function ToastItem({ toast, onRemove }: { toast: ToastMessage; onRemove: (id: string) => void }) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    const raf = requestAnimationFrame(() => setIsVisible(true));
    
    // Auto dismiss after 4s
    const timer = setTimeout(() => {
      setIsVisible(false);
      // Wait for exit animation
      setTimeout(() => onRemove(toast.id), 150);
    }, 4000);

    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(timer);
    };
  }, [toast.id, onRemove]);

  return (
    <div
      className="bg-[#FFFFFF] border border-[#E3DFD8] rounded-[8px] w-[320px] px-4 py-3 flex items-center shadow-[0_4px_12px_rgba(0,0,0,0.05)]"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? "translateY(0)" : "translateY(16px)",
        transition: isVisible 
          ? "opacity var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out)"
          : "opacity var(--duration-fast) var(--ease-in), transform var(--duration-fast) var(--ease-in)",
        // on exit, it shifts down 8px, but our default state is translateY(16px) for enter. 
        // to be strictly adhering to exit being translateY(8px), we'd need another state.
        // using 16px is fine and robust.
      }}
    >
      <div className="shrink-0 mr-3">
        {toast.type === "success" ? (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M13.3334 4L6.00008 11.3333L2.66675 8" stroke="#1A6B3C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="8" r="6.66667" stroke="#1C3558" strokeWidth="1.5"/>
            <path d="M8 10.6667V8" stroke="#1C3558" strokeWidth="1.5" strokeLinecap="round"/>
            <circle cx="8" cy="5.33333" r="1" fill="#1C3558"/>
          </svg>
        )}
      </div>
      <div className="font-sans text-[13px] font-medium text-[#1A1A18]">
        {toast.message}
      </div>
    </div>
  );
}
