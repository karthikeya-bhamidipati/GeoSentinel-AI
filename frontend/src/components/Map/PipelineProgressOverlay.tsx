"use client";

// =============================================================================
// GeoSentinel AI — Pipeline Progress Overlay
// Shows named steps as they complete during analysis (no spinners alone)
// =============================================================================

import React from "react";

export const PIPELINE_STEPS = [
  { id: "aoi", label: "AOI Validated" },
  { id: "search", label: "Searching CDSE" },
  { id: "download", label: "Downloading Scenes" },
  { id: "preprocess", label: "Preprocessing Rasters" },
  { id: "features", label: "Computing Features" },
  { id: "ai", label: "Running AI Segmentation" },
  { id: "temporal", label: "Temporal Analysis" },
  { id: "recommendations", label: "Generating Recommendations" },
  { id: "report", label: "Building Report" },
] as const;

interface PipelineProgressOverlayProps {
  isVisible: boolean;
  message: string;
  completedSteps?: string[];
}

export function PipelineProgressOverlay({
  isVisible,
  message,
  completedSteps = [],
}: PipelineProgressOverlayProps) {
  if (!isVisible) return null;

  const normalizedMessage = message.toLowerCase();
  const runningStepId =
    PIPELINE_STEPS.find(
      (step) =>
        normalizedMessage.includes(step.id) ||
        normalizedMessage.includes(step.label.toLowerCase().split(" ")[0])
    )?.id ?? null;
  const runningIdx = PIPELINE_STEPS.findIndex(
    (step) => step.id === runningStepId
  );

  return (
    <div className="pipeline-overlay" role="status" aria-live="polite">
      {/* Header */}
      <div className="pipeline-header">
        <div className="spinner spinner-sm" style={{ borderColor: "rgba(255,255,255,0.3)", borderTopColor: "white" }} />
        <span>Processing Analysis</span>
      </div>

      {/* Steps */}
      {PIPELINE_STEPS.map((step, idx) => {
        const isDone = completedSteps.includes(step.id);
        const isRunning = idx === runningIdx && !isDone;

        return (
          <div
            key={step.id}
            className={`pipeline-step ${isDone ? "done" : isRunning ? "running" : "pending"}`}
          >
            <div className="pipeline-step-icon">
              {isDone ? (
                <svg viewBox="0 0 14 14" fill="currentColor" style={{ width: 14, height: 14 }}>
                  <path fillRule="evenodd" d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z" clipRule="evenodd"/>
                </svg>
              ) : isRunning ? (
                <div className="spinner" style={{ width: 10, height: 10, borderWidth: 1.5, borderColor: "rgba(29,111,164,0.3)", borderTopColor: "var(--color-primary)" }} />
              ) : (
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--color-border)", margin: "0 auto" }} />
              )}
            </div>
            <span>{step.label}</span>
          </div>
        );
      })}

      {/* Status text */}
      {message && (
        <div style={{ padding: "6px 12px", fontSize: 10, color: "var(--color-text-muted)", borderTop: "1px solid var(--color-border)", fontFamily: "var(--font-mono)" }}>
          {message}
        </div>
      )}
    </div>
  );
}
