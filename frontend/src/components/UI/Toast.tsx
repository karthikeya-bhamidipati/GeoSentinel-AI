"use client";

// =============================================================================
// GeoSentinel AI — Toast Notification Component
// Lightweight, zero-dependency toast system
// =============================================================================

import { useEffect, useState, useCallback } from "react";

export type ToastType = "success" | "error" | "info" | "warning";

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
  exiting?: boolean;
}

const TOAST_ICONS: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  info: "ℹ",
  warning: "⚠",
};

interface ToastProps {
  item: ToastItem;
  onRemove: (id: string) => void;
}

function Toast({ item, onRemove }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(item.id);
    }, 5000);
    return () => clearTimeout(timer);
  }, [item.id, onRemove]);

  return (
    <div
      className={`toast toast-${item.type}${item.exiting ? " toast-exit" : ""}`}
      role="alert"
    >
      <span className="toast-icon">{TOAST_ICONS[item.type]}</span>
      <span className="toast-message">{item.message}</span>
      <button
        className="toast-close"
        onClick={() => onRemove(item.id)}
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
}

interface ToastContainerProps {
  toasts: ToastItem[];
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((t) => (
        <Toast key={t.id} item={t} onRemove={onRemove} />
      ))}
    </div>
  );
}
