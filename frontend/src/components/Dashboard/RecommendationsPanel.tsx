"use client";

// =============================================================================
// GeoSentinel AI — Recommendations Panel
// =============================================================================

import { useState } from "react";
import type { Recommendation, Severity } from "@/types";

interface RecommendationsPanelProps {
  recommendations: Recommendation[];
}

const SEVERITY_BADGE: Record<Severity, string> = {
  CRITICAL: "badge badge-critical",
  HIGH: "badge badge-high",
  MEDIUM: "badge badge-medium",
  LOW: "badge badge-low",
};

export function RecommendationsPanel({
  recommendations,
}: RecommendationsPanelProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="panel">
      <div className="panel-title">
        Recommendations ({recommendations.length})
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {recommendations.map((rec) => (
          <div
            key={rec.rule_id}
            style={{
              background: "var(--color-bg)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              overflow: "hidden",
              cursor: "pointer",
            }}
            onClick={() =>
              setExpanded(expanded === rec.rule_id ? null : rec.rule_id)
            }
          >
            {/* Header */}
            <div
              style={{
                padding: "8px 12px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span className={SEVERITY_BADGE[rec.severity as Severity]}>
                {rec.severity}
              </span>
              <span
                style={{
                  fontSize: "0.78rem",
                  fontWeight: 500,
                  flex: 1,
                  color: "var(--color-text)",
                }}
              >
                {rec.title}
              </span>
              <span
                style={{
                  fontSize: "0.7rem",
                  color: "var(--color-text-muted)",
                }}
              >
                {expanded === rec.rule_id ? "▲" : "▼"}
              </span>
            </div>

            {/* Expanded Content */}
            {expanded === rec.rule_id && (
              <div
                style={{
                  padding: "0 12px 10px",
                  borderTop: "1px solid var(--color-border)",
                }}
              >
                <div
                  style={{
                    fontSize: "0.7rem",
                    color: "var(--color-accent)",
                    marginTop: "8px",
                    marginBottom: "4px",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Why
                </div>
                <p
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--color-text-muted)",
                    marginBottom: "8px",
                    fontStyle: "italic",
                  }}
                >
                  {rec.why}
                </p>
                <div
                  style={{
                    fontSize: "0.7rem",
                    color: "var(--color-accent)",
                    marginBottom: "4px",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  Action
                </div>
                <p
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--color-text)",
                  }}
                >
                  {rec.recommendation}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
