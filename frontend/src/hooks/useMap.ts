"use client";

// =============================================================================
// GeoSentinel AI — useMap Hook
// =============================================================================

import { useState, useCallback } from "react";
import type { AOIGeometry, LatLng } from "@/types";

export interface Layer {
  id: string;
  name: string;
  color: string;
  visible: boolean;
  type: "base" | "analysis" | "reference";
}

export const INITIAL_LAYERS: Layer[] = [
  { id: "satellite", name: "Satellite Imagery", color: "#888", visible: true, type: "base" },
  { id: "osm", name: "OpenStreetMap", color: "#1d6fa4", visible: false, type: "base" },
  { id: "hmr_boundary", name: "HMR Boundary", color: "#1d6fa4", visible: true, type: "reference" },
  { id: "aoi", name: "Area of Interest", color: "#e67e22", visible: true, type: "reference" },
  { id: "image_t1", name: "Satellite T1", color: "#888", visible: false, type: "analysis" },
  { id: "image_t2", name: "Satellite T2", color: "#888", visible: false, type: "analysis" },
  { id: "segmentation_t1", name: "Classification T1", color: "#2d7a3e", visible: false, type: "analysis" },
  { id: "segmentation_t2", name: "Classification T2", color: "#c0392b", visible: false, type: "analysis" },
  { id: "ndvi_change", name: "NDVI Change", color: "#2d7a3e", visible: false, type: "analysis" },
  { id: "ndbi_change", name: "NDBI Change", color: "#c0392b", visible: false, type: "analysis" },
];

interface MapState {
  drawnAOI: AOIGeometry | null;
  isDrawingMode: boolean;
  layers: Layer[];
}

/**
 * useMap — manages AOI drawing state and map layers.
 *
 * Tracks the user-drawn polygon, drawing mode activation, and which map layers are visible.
 */
export function useMap() {
  const [state, setState] = useState<MapState>({
    drawnAOI: null,
    isDrawingMode: false,
    layers: INITIAL_LAYERS,
  });

  const setDrawnAOI = useCallback((aoi: AOIGeometry | null) => {
    setState((prev) => ({ ...prev, drawnAOI: aoi }));
  }, []);

  const setDrawingMode = useCallback((active: boolean) => {
    setState((prev) => ({ ...prev, isDrawingMode: active }));
  }, []);

  const clearAOI = useCallback(() => {
    setState((prev) => ({ ...prev, drawnAOI: null }));
  }, []);

  const toggleLayer = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      layers: prev.layers.map((l) => (l.id === id ? { ...l, visible: !l.visible } : l))
    }));
  }, []);

  return {
    ...state,
    setDrawnAOI,
    setDrawingMode,
    clearAOI,
    toggleLayer,
  };
}
