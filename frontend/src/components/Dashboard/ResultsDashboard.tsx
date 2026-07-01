"use client";

// =============================================================================
// GeoSentinel AI — Results Dashboard
// =============================================================================

import type { AnalysisResult } from "@/types";
import { LAND_COVER_CLASSES } from "@/types";
import { ChangeChart } from "./ChangeChart";
import { RecommendationsPanel } from "./RecommendationsPanel";
import { DownloadPanel } from "./DownloadPanel";
import { StatisticsPanel } from "./StatisticsPanel";

interface ResultsDashboardProps {
  result: AnalysisResult;
}

export function ResultsDashboard({ result }: ResultsDashboardProps) {
  return (
    <>
      {/* Summary Header */}
      <div className="panel">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "0.75rem",
          }}
        >
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "0.9rem",
              fontWeight: 700,
              color: "var(--color-text)",
            }}
          >
            Analysis Results
          </div>
          <div
            style={{
              fontSize: "0.7rem",
              color: "var(--color-green)",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>✓</span> Complete
          </div>
        </div>

        <div className="stat-grid">
          <div className="stat-item">
            <div className="stat-label">Period</div>
            <div
              className="stat-value"
              style={{ fontSize: "0.75rem" }}
            >
              {result.date1} → {result.date2}
            </div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Study Area</div>
            <div className="stat-value" style={{ fontSize: "0.8rem" }}>
              {result.area_change.total_area_km2?.toFixed(1)} km²
            </div>
          </div>
        </div>
      </div>

      {/* Area Change Chart */}
      {result.area_change.rows && result.area_change.rows.length > 0 && (
        <div className="panel">
          <div className="panel-title">Land Cover Change</div>
          <ChangeChart rows={result.area_change.rows} />
        </div>
      )}

      {/* Statistics */}
      <StatisticsPanel temporalStats={result.temporal_stats} />

      {/* Recommendations */}
      {result.recommendations.length > 0 && (
        <RecommendationsPanel
          recommendations={result.recommendations}
        />
      )}

      {/* Download */}
      <DownloadPanel jobId={result.job_id} outputs={result.outputs} />
    </>
  );
}
