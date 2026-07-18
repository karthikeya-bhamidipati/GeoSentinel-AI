"use client";

// =============================================================================
// GeoSentinel AI — MapLegend Component
// Dynamic floating legend that adapts to visible analysis layers
// =============================================================================

import { useState } from "react";
import type { Layer } from "@/hooks/useMap";

interface MapLegendProps {
  layers: Layer[];
  blinkMode?: boolean;
}

const LAND_COVER_CLASSES = [
  { label: "Background", color: "#000000" },
  { label: "Urban", color: "#DC143C" },
  { label: "Vegetation", color: "#228B22" },
  { label: "Water", color: "#1E90FF" },
  { label: "Barren", color: "#D2B48C" },
  { label: "Agriculture", color: "#FFD700" },
];

export function MapLegend({ layers, blinkMode }: MapLegendProps) {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const visibleAnalysis = layers.filter(
    (l) => l.type === "analysis" && l.visible && !dismissed.has(l.id)
  );

  // If blinkMode is active, always show the classification legend (unless dismissed)
  const showClassification = blinkMode || visibleAnalysis.some(
    (l) => l.id === "segmentation_t1" || l.id === "segmentation_t2"
  );
  
  const showNDVI = visibleAnalysis.some((l) => l.id === "ndvi_change");
  const showNDBI = visibleAnalysis.some((l) => l.id === "ndbi_change");

  // Only hide entirely if nothing is to be shown
  if (!showClassification && !showNDVI && !showNDBI) return null;

  const handleDismiss = () => {
    setDismissed(new Set(visibleAnalysis.map((l) => l.id)));
  };

  return (
    <div className="map-legend">
      <div className="map-legend-header">
        <span className="map-legend-title">Legend</span>
        <button
          className="map-legend-close"
          onClick={handleDismiss}
          aria-label="Close legend"
        >
          ×
        </button>
      </div>

      {showClassification && (
        <div className="map-legend-section">
          <div className="map-legend-section-title">Land Cover Classes</div>
          {LAND_COVER_CLASSES.map((cls) => (
            <div className="map-legend-item" key={cls.label}>
              <span
                className="map-legend-swatch"
                style={{ background: cls.color }}
              />
              <span className="map-legend-label">{cls.label}</span>
            </div>
          ))}
        </div>
      )}

      {showNDVI && (
        <div className="map-legend-section">
          <div className="map-legend-section-title">NDVI Change</div>
          <div className="map-legend-gradient-row">
            <span className="map-legend-gradient-label">Loss</span>
            <div
              className="map-legend-gradient-bar"
              style={{
                background:
                  "linear-gradient(to right, #d32f2f, #ffffff, #2e7d32)",
              }}
            />
            <span className="map-legend-gradient-label">Gain</span>
          </div>
        </div>
      )}

      {showNDBI && (
        <div className="map-legend-section">
          <div className="map-legend-section-title">NDBI Change</div>
          <div className="map-legend-gradient-row">
            <span className="map-legend-gradient-label">Dec</span>
            <div
              className="map-legend-gradient-bar"
              style={{
                background:
                  "linear-gradient(to right, #1565c0, #ffffff, #c62828)",
              }}
            />
            <span className="map-legend-gradient-label">Inc</span>
          </div>
        </div>
      )}
    </div>
  );
}
