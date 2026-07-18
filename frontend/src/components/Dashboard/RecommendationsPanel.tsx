"use client";

// =============================================================================
// GeoSentinel AI — Recommendations Panel
// Accordion-style recommendation cards with severity badges and evidence
// =============================================================================

import { useState } from "react";
import type { Recommendation, Severity } from "@/types";

interface RecommendationsPanelProps {
  recommendations: Recommendation[];
}

const SEVERITY_ORDER: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

export function RecommendationsPanel({ recommendations }: RecommendationsPanelProps) {

  // Sort by severity order
  const sorted = [...recommendations].sort(
    (a, b) =>
      SEVERITY_ORDER.indexOf(a.severity as Severity) -
      SEVERITY_ORDER.indexOf(b.severity as Severity)
  );

  const counts = SEVERITY_ORDER.reduce<Record<string, number>>((acc, sev) => {
    acc[sev] = recommendations.filter((r) => r.severity === sev).length;
    return acc;
  }, {});

  return (
    <div>
      {/* Severity summary pills */}
      <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap", marginBottom: "var(--space-3)" }}>
        {SEVERITY_ORDER.map((sev) =>
          counts[sev] > 0 ? (
            <span key={sev} className={`badge badge-${sev.toLowerCase()}`}>
              {counts[sev]} {sev}
            </span>
          ) : null
        )}
      </div>

      {/* Recommendation cards */}
      {sorted.map((rec) => (
        <div key={rec.rule_id} className="rec-card">
          {/* Header — always visible */}
          <div
            className="rec-card-header"
            style={{ cursor: "default" }}
          >
            <span className={`badge badge-${rec.severity.toLowerCase()}`} style={{ flexShrink: 0 }}>
              {rec.severity}
            </span>
            <span className="rec-card-title">{rec.title}</span>
          </div>

          {/* Category & rule meta */}
          <div style={{ padding: "4px var(--space-3) 0", display: "flex", gap: "var(--space-2)" }}>
            <span className="text-xs text-muted">{rec.category}</span>
            <span className="text-xs text-muted">·</span>
            <span className="text-xs text-muted" style={{ fontFamily: "var(--font-mono)" }}>
              {rec.rule_id}
            </span>
          </div>

          {/* Expanded body (now always visible) */}
          <div className="rec-card-body" style={{ borderTop: "1px solid var(--color-border)" }}>
            <div className="rec-card-label">Evidence (Why this was triggered)</div>
            <div
              className="rec-card-value"
              style={{
                background: "var(--color-surface-alt)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-sm)",
                padding: "var(--space-2) var(--space-3)",
                fontStyle: "italic",
                color: "var(--color-text-secondary)",
                fontSize: "var(--font-size-xs)",
              }}
            >
              {rec.why}
            </div>

            <div className="rec-card-label">Recommended Action</div>
            <div className="rec-card-value">{rec.recommendation}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
