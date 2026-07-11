"use client";

// =============================================================================
// GeoSentinel AI — useToast Hook
// Returns { toast, toasts, removeToast } for the toast notification system
// =============================================================================

import { useState, useCallback } from "react";
import type { ToastType, ToastItem } from "@/components/UI/Toast";

let toastCounter = 0;

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const toast = useCallback((message: string, type: ToastType = "info") => {
    const id = `toast-${++toastCounter}-${Date.now()}`;
    setToasts((prev) => [...prev, { id, message, type }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    // Trigger exit animation first
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, exiting: true } : t))
    );
    // Then remove after animation completes
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 300);
  }, []);

  return { toast, toasts, removeToast };
}
