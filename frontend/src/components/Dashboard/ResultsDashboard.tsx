"use client";

// =============================================================================
// GeoSentinel AI — Results Dashboard
// Professional GIS-style results display with charts, statistics, recommendations
// =============================================================================

import React, { useState } from "react";
import type { AnalysisResult } from "@/types";
import { LAND_COVER_CLASSES } from "@/types";
import dynamic from "next/dynamic";
const ChangeChart = dynamic(() => import("./ChangeChart").then(mod => mod.ChangeChart), { ssr: false });
import { RecommendationsPanel } from "./RecommendationsPanel";
import { StatisticsPanel } from "./StatisticsPanel";

interface ResultsDashboardProps {
  result: AnalysisResult;
}

type DashboardTab = "overview" | "landcover" | "temporal" | "recommendations";

export function ResultsDashboard({ result }: ResultsDashboardProps) {
  const [activeTab, setActiveTab] = useState<DashboardTab>("overview");

  const tabs: { id: DashboardTab; label: string; count?: number }[] = [
    { id: "overview", label: "Overview" },
    { id: "landcover", label: "Land Cover" },
    { id: "temporal", label: "Temporal" },
    {
      id: "recommendations",
      label: "Recommendations",
      count: result.recommendations.length,
    },
  ];

  // Key metrics for overview
  const ndvi = result.temporal_stats?.ndvi_change;
  const ndbi = result.temporal_stats?.ndbi_change;
  const seg = result.temporal_stats?.segmentation_change;

  return (
    <div>
      {/* Sub-tabs */}
      <div className="tabs" style={{ position: "sticky", top: 0, zIndex: 10 }}>
        {tabs.map(({ id, label, count }) => (
          <button
            key={id}
            id={`dashboard-tab-${id}`}
            className={`tab${activeTab === id ? " active" : ""}`}
            onClick={() => setActiveTab(id)}
          >
            {label}
            {count != null && count > 0 && (
              <span
                style={{
                  marginLeft: 4,
                  padding: "0px 5px",
                  borderRadius: 8,
                  background: activeTab === id ? "var(--color-primary)" : "var(--color-border)",
                  color: activeTab === id ? "white" : "var(--color-text-muted)",
                  fontSize: 9,
                  fontWeight: 700,
                }}
              >
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-3">

        {/* --- OVERVIEW --- */}
        {activeTab === "overview" && (
          <div>
            {/* Key metric cards */}
            <div className="metric-grid" style={{ marginBottom: "var(--space-3)" }}>
              <div className="metric-card">
                <div className="metric-value neutral" style={{ fontSize: 18 }}>
                  {result.area_change?.total_area_km2?.toFixed(1) ?? "—"}
                </div>
                <div className="metric-label">Total Area (km²)</div>
              </div>
              <div className="metric-card">
                <div className={`metric-value ${ndvi?.mean_delta != null ? (ndvi.mean_delta < 0 ? "negative" : "positive") : ""}`} style={{ fontSize: 18 }}>
                  {ndvi?.mean_delta != null ? (ndvi.mean_delta > 0 ? "+" : "") + ndvi.mean_delta.toFixed(3) : "—"}
                </div>
                <div className="metric-label">ΔNDVI (Mean)</div>
              </div>
              <div className="metric-card">
                <div className={`metric-value ${ndbi?.urban_increase_pct != null && ndbi.urban_increase_pct > 5 ? "negative" : "positive"}`} style={{ fontSize: 18 }}>
                  {ndbi?.urban_increase_pct != null ? `+${ndbi.urban_increase_pct.toFixed(1)}%` : "—"}
                </div>
                <div className="metric-label">Urban Increase</div>
              </div>
              <div className="metric-card">
                <div className={`metric-value ${seg?.vegetation_loss_pixels != null && seg.vegetation_loss_pixels > 0 ? "negative" : "positive"}`} style={{ fontSize: 18 }}>
                  {seg?.changed_pct != null ? `${seg.changed_pct.toFixed(1)}%` : "—"}
                </div>
                <div className="metric-label">Changed Area</div>
              </div>
            </div>

            {/* Scene info */}
            <div className="panel">
              <div className="panel-header"><span className="panel-title">Satellite Scenes</span></div>
              <div className="panel-body" style={{ padding: 0 }}>
                <table className="stats-table">
                  <thead>
                    <tr>
                      <th>Epoch</th>
                      <th>Date</th>
                      <th>Scene ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ fontFamily: "var(--font-sans)", color: "var(--color-primary)", fontWeight: 600 }}>T1</td>
                      <td>{result.date1}</td>
                      <td style={{ maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis" }}>{result.scene_t1_id}</td>
                    </tr>
                    <tr>
                      <td style={{ fontFamily: "var(--font-sans)", color: "var(--color-error)", fontWeight: 600 }}>T2</td>
                      <td>{result.date2}</td>
                      <td style={{ maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis" }}>{result.scene_t2_id}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* --- LAND COVER --- */}
        {activeTab === "landcover" && (
          <div>
            {result.area_change?.rows?.length > 0 ? (
              <>
                <div className="panel">
                  <div className="panel-header"><span className="panel-title">Land Cover Change Chart</span></div>
                  <div className="panel-body">
                    <ChangeChart rows={result.area_change.rows} />
                  </div>
                </div>

                <div className="panel">
                  <div className="panel-header"><span className="panel-title">Area Statistics Table</span></div>
                  <table className="stats-table">
                    <thead>
                      <tr>
                        <th>Class</th>
                        <th>T1 (km²)</th>
                        <th>T2 (km²)</th>
                        <th>Change</th>
                        <th>Δ%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.area_change.rows.map((row) => {
                        const cls = LAND_COVER_CLASSES[row.class_id];
                        return (
                          <tr key={row.class_id}>
                            <td style={{ fontFamily: "var(--font-sans)" }}>
                              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                                <span style={{ width: 8, height: 8, borderRadius: 2, background: cls?.color, display: "inline-block", flexShrink: 0 }} />
                                {row.class_name}
                              </span>
                            </td>
                            <td>{row.t1_area_km2.toFixed(2)}</td>
                            <td>{row.t2_area_km2.toFixed(2)}</td>
                            <td style={{ color: row.change_km2 < 0 ? "var(--color-error)" : row.change_km2 > 0 ? "var(--color-success)" : undefined }}>
                              {row.change_km2 > 0 ? "+" : ""}{row.change_km2.toFixed(2)}
                            </td>
                            <td style={{ color: row.change_pct < 0 ? "var(--color-error)" : row.change_pct > 0 ? "var(--color-success)" : undefined }}>
                              {row.change_pct > 0 ? "+" : ""}{row.change_pct.toFixed(1)}%
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div className="empty-state">
                <p className="empty-state-text">No land cover statistics available.</p>
              </div>
            )}
          </div>
        )}

        {/* --- TEMPORAL --- */}
        {activeTab === "temporal" && (
          <StatisticsPanel temporalStats={result.temporal_stats} />
        )}

        {/* --- RECOMMENDATIONS --- */}
        {activeTab === "recommendations" && (
          result.recommendations.length > 0 ? (
            <RecommendationsPanel recommendations={result.recommendations} />
          ) : (
            <div className="empty-state">
              <p className="empty-state-text">No recommendations triggered for this analysis.</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}
