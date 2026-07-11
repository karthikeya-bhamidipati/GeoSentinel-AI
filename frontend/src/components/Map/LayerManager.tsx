"use client";

// =============================================================================
// GeoSentinel AI — Layer Manager
// Toggle visibility of geospatial layers on the map
// =============================================================================

import React from "react";
import type { Layer } from "@/hooks/useMap";

const TYPE_LABELS: Record<Layer["type"], string> = {
  base: "Base Maps",
  reference: "Reference Layers",
  analysis: "Analysis Results",
};

interface LayerManagerProps {
  layers: Layer[];
  onToggleLayer: (id: string) => void;
}

export function LayerManager({ layers, onToggleLayer }: LayerManagerProps) {
  const groupedLayers = layers.reduce<Record<Layer["type"], Layer[]>>(
    (acc, layer) => {
      if (!acc[layer.type]) acc[layer.type] = [];
      acc[layer.type].push(layer);
      return acc;
    },
    { base: [], reference: [], analysis: [] }
  );

  return (
    <div>
      {(["base", "reference", "analysis"] as Layer["type"][]).map((type) => (
        <div key={type} className="form-section">
          <div className="form-section-title">{TYPE_LABELS[type]}</div>
          {groupedLayers[type].map((layer) => (
            <div key={layer.id} className="layer-item">
              <div
                className="layer-color-dot"
                style={{ background: layer.color }}
              />
              <span className="layer-name">{layer.name}</span>
              <button
                id={`layer-toggle-${layer.id}`}
                className={`layer-toggle ${layer.visible ? "on" : ""}`}
                onClick={() => onToggleLayer(layer.id)}
                aria-pressed={layer.visible}
                aria-label={`Toggle ${layer.name}`}
              />
            </div>
          ))}
        </div>
      ))}

      <div
        style={{
          padding: "var(--space-2) var(--space-3)",
          background: "var(--color-surface-alt)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-sm)",
          fontSize: "var(--font-size-xs)",
          color: "var(--color-text-muted)",
        }}
      >
        Analysis result layers become available after a completed analysis job.
      </div>
    </div>
  );
}
