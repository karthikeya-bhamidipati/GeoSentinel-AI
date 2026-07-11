"use client";

// =============================================================================
// GeoSentinel AI — Right Results Panel
// Professional GIS-style tabbed results panel
// =============================================================================

import React, { useState } from "react";
import type { AnalysisResult } from "@/types";
import { ResultsDashboard } from "@/components/Dashboard/ResultsDashboard";

interface RightPanelProps {
  result: AnalysisResult | null;
  isLoading: boolean;
  progressMessage: string;
  jobId: string | null;
}

export function RightPanel({ result, isLoading, progressMessage, jobId }: RightPanelProps) {
  const [activeTab, setActiveTab] = useState<"results" | "metadata">("results");

  // --- Empty state ---
  if (!result && !isLoading) {
    return (
      <aside
        className="right-panel"
        aria-label="Analysis results"
      >
        <div
          style={{
            padding: "var(--space-3) var(--space-4)",
            borderBottom: "1px solid var(--color-border)",
            background: "var(--color-surface-alt)",
            flexShrink: 0,
          }}
        >
          <div className="content-panel-title">Results</div>
        </div>
        <div className="empty-state">
          <svg className="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
          </svg>
          <p className="empty-state-title">No Results Yet</p>
          <p className="empty-state-text">
            Draw an AOI on the map, configure analysis parameters, then click Run Analysis.
          </p>
        </div>
      </aside>
    );
  }

  // --- Loading state ---
  if (isLoading && !result) {
    return (
      <aside className="right-panel" aria-label="Analysis results">
        <div style={{ padding: "var(--space-3) var(--space-4)", borderBottom: "1px solid var(--color-border)", background: "var(--color-surface-alt)", flexShrink: 0 }}>
          <div className="content-panel-title">Processing</div>
        </div>
        <div className="empty-state">
          <div className="spinner spinner-lg" />
          <p className="empty-state-title">Running Analysis</p>
          <p className="empty-state-text" style={{ fontFamily: "var(--font-mono)", maxWidth: "220px" }}>
            {progressMessage || "Processing…"}
          </p>
          {jobId && (
            <p className="text-xs text-muted" style={{ fontFamily: "var(--font-mono)", marginTop: "var(--space-2)" }}>
              Job: {jobId.substring(0, 8)}…
            </p>
          )}
        </div>
      </aside>
    );
  }

  // --- Results state ---
  return (
    <aside className="right-panel" aria-label="Analysis results">
      {/* Panel Header */}
      <div
        style={{
          padding: "var(--space-2) var(--space-3)",
          borderBottom: "1px solid var(--color-border)",
          background: "var(--color-surface-alt)",
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div>
          <div className="content-panel-title">Analysis Results</div>
          {result && (
            <div className="text-xs text-muted" style={{ marginTop: 1, fontFamily: "var(--font-mono)" }}>
              {result.date1} → {result.date2} · {result.job_id.substring(0, 8)}
            </div>
          )}
        </div>
        {result?.success && (
          <span className="badge badge-low" style={{ flexShrink: 0 }}>Complete</span>
        )}
        {result && !result.success && (
          <span className="badge badge-critical" style={{ flexShrink: 0 }}>Failed</span>
        )}
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab${activeTab === "results" ? " active" : ""}`}
          onClick={() => setActiveTab("results")}
          id="tab-results"
        >
          Statistics & Recommendations
        </button>
        <button
          className={`tab${activeTab === "metadata" ? " active" : ""}`}
          onClick={() => setActiveTab("metadata")}
          id="tab-metadata"
        >
          Metadata
        </button>
      </div>

      {/* Content */}
      <div className="overflow-y-auto flex-1">
        {activeTab === "results" && result && (
          <ResultsDashboard result={result} />
        )}
        {activeTab === "metadata" && result && (
          <MetadataPanel result={result} />
        )}
      </div>
    </aside>
  );
}

function MetadataPanel({ result }: { result: AnalysisResult }) {
  const rows = [
    { label: "Job ID", value: result.job_id, mono: true },
    { label: "Date T1", value: result.date1 },
    { label: "Date T2", value: result.date2 },
    { label: "Scene T1", value: result.scene_t1_id, mono: true },
    { label: "Scene T2", value: result.scene_t2_id, mono: true },
    { label: "Cloud Cover T1", value: result.metadata?.cloud_cover_t1 != null ? `${result.metadata.cloud_cover_t1}%` : "—" },
    { label: "Cloud Cover T2", value: result.metadata?.cloud_cover_t2 != null ? `${result.metadata.cloud_cover_t2}%` : "—" },
    { label: "Elapsed Time", value: result.metadata?.elapsed_seconds != null ? `${result.metadata.elapsed_seconds}s` : "—" },
    { label: "Status", value: result.success ? "Success" : "Failed" },
  ];

  return (
    <div className="p-3">
      <div className="panel">
        <div className="panel-header"><span className="panel-title">Job Information</span></div>
        <table className="stats-table">
          <tbody>
            {rows.map(({ label, value, mono }) => (
              <tr key={label}>
                <td style={{ fontFamily: "var(--font-sans)", fontWeight: 500, color: "var(--color-text-secondary)", fontSize: 11 }}>{label}</td>
                <td style={{ fontFamily: mono ? "var(--font-mono)" : undefined, textAlign: "right", fontSize: 11, wordBreak: "break-all" }}>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {result.error && (
        <div style={{ padding: "var(--space-3)", background: "var(--color-error-bg)", border: "1px solid var(--color-error-border)", borderRadius: "var(--radius-sm)", fontSize: "var(--font-size-sm)", color: "var(--color-error)" }}>
          <strong>Error:</strong> {result.error}
        </div>
      )}
    </div>
  );
}
