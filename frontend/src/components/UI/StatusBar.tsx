"use client";

// =============================================================================
// GeoSentinel AI — Status Bar
// =============================================================================

import type { JobStatus } from "@/types";

interface StatusBarProps {
  status: JobStatus | null;
  message: string;
  error: string | null;
  onClose: () => void;
}

export function StatusBar({ status, message, error, onClose }: StatusBarProps) {
  const dotClass = error
    ? "failed"
    : status === "running" || status === "queued"
    ? "running"
    : "completed";

  const displayMessage = error
    ? `Error: ${error}`
    : message || "Processing ...";

  return (
    <div className="status-bar">
      <div className={`status-dot ${dotClass}`} />

      <span style={{ color: "var(--color-text)" }}>{displayMessage}</span>

      {(status === "completed" || error) && (
        <button
          onClick={onClose}
          style={{
            background: "none",
            border: "none",
            color: "var(--color-text-muted)",
            cursor: "pointer",
            fontSize: "0.8rem",
            padding: "0 4px",
            marginLeft: "4px",
          }}
          aria-label="Close status bar"
        >
          ✕
        </button>
      )}
    </div>
  );
}
