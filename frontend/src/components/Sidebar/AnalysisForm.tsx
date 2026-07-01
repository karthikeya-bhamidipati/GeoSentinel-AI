"use client";

// =============================================================================
// GeoSentinel AI — Analysis Form
// =============================================================================

import { useState } from "react";

interface AnalysisFormProps {
  onSubmit: (date1: string, date2: string, maxCloudCover: number) => void;
  hasAOI: boolean;
  isLoading: boolean;
  onClearAOI: () => void;
}

export function AnalysisForm({
  onSubmit,
  hasAOI,
  isLoading,
  onClearAOI,
}: AnalysisFormProps) {
  const [date1, setDate1] = useState("2023-01-15");
  const [date2, setDate2] = useState("2024-01-15");
  const [maxCloudCover, setMaxCloudCover] = useState(10);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasAOI) return;
    onSubmit(date1, date2, maxCloudCover);
  };

  return (
    <div>
      {/* Title */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "1rem",
            fontWeight: 700,
            color: "var(--color-text)",
            marginBottom: "4px",
          }}
        >
          Land Cover Analysis
        </h1>
        <p style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
          Sentinel-2 L2A · HMR · CDSE
        </p>
      </div>

      {/* AOI Status */}
      <div className="panel" style={{ marginBottom: "1rem" }}>
        <div className="panel-title">Area of Interest</div>

        {hasAOI ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                color: "var(--color-green)",
                fontSize: "0.8rem",
                fontWeight: 500,
              }}
            >
              <span>✓</span>
              <span>AOI defined</span>
            </div>
            <button
              className="btn btn-ghost btn-sm"
              onClick={onClearAOI}
              type="button"
            >
              Clear
            </button>
          </div>
        ) : (
          <p
            style={{
              fontSize: "0.8rem",
              color: "var(--color-text-muted)",
              fontStyle: "italic",
            }}
          >
            Click "Draw AOI" on the map to define your study area.
          </p>
        )}
      </div>

      {/* Analysis Parameters */}
      <form onSubmit={handleSubmit}>
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <div className="panel-title">Time Period</div>

          <div className="form-group">
            <label className="form-label" htmlFor="date1">
              Date 1 (T1 — Earlier)
            </label>
            <input
              id="date1"
              type="date"
              className="form-input"
              value={date1}
              onChange={(e) => setDate1(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="date2">
              Date 2 (T2 — Later)
            </label>
            <input
              id="date2"
              type="date"
              className="form-input"
              value={date2}
              onChange={(e) => setDate2(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="panel" style={{ marginBottom: "1rem" }}>
          <div className="panel-title">Scene Selection</div>

          <div className="form-group">
            <label className="form-label" htmlFor="cloud-cover">
              Max Cloud Cover: {maxCloudCover}%
            </label>
            <input
              id="cloud-cover"
              type="range"
              min={0}
              max={50}
              step={5}
              value={maxCloudCover}
              onChange={(e) => setMaxCloudCover(Number(e.target.value))}
              style={{
                width: "100%",
                accentColor: "var(--color-accent)",
              }}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "0.65rem",
                color: "var(--color-text-muted)",
                marginTop: "2px",
              }}
            >
              <span>0%</span>
              <span>50%</span>
            </div>
          </div>
        </div>

        {/* Info */}
        <div
          className="panel"
          style={{ marginBottom: "1rem", fontSize: "0.75rem" }}
        >
          <div className="panel-title">Analysis Pipeline</div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "6px",
              color: "var(--color-text-muted)",
            }}
          >
            {[
              "1. CDSE STAC search & download",
              "2. Cloud masking + normalization",
              "3. Feature engineering (12 channels)",
              "4. U-Net segmentation inference",
              "5. NDVI / NDBI temporal analysis",
              "6. Area statistics",
              "7. Rule-based recommendations",
              "8. PDF + CSV + GeoTIFF export",
            ].map((step) => (
              <div key={step} style={{ display: "flex", gap: "8px" }}>
                <span style={{ color: "var(--color-accent)", flexShrink: 0 }}>
                  ›
                </span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-full"
          disabled={!hasAOI || isLoading}
          id="run-analysis-btn"
        >
          {isLoading ? (
            <>
              <div className="spinner" style={{ width: 16, height: 16 }} />
              Running Analysis ...
            </>
          ) : (
            <>🛰️ Run Analysis</>
          )}
        </button>
      </form>
    </div>
  );
}
