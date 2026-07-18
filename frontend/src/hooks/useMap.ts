"use client";

// =============================================================================
// GeoSentinel AI — useMap Hook (v2.0)
// Enhanced with blink mode, guided tour, layer reordering, and zone support
// =============================================================================

import { useState, useCallback, useRef } from "react";
import type { AOIGeometry } from "@/types";

export interface Layer {
  id: string;
  name: string;
  color: string;
  visible: boolean;
  type: "base" | "analysis" | "reference";
  opacity?: number;
}

export const INITIAL_LAYERS: Layer[] = [
  { id: "dark",      name: "Dark Map",           color: "#38bdf8", visible: false, type: "base",      opacity: 1 },
  { id: "satellite",  name: "Satellite Imagery",  color: "#888",    visible: true,  type: "base",      opacity: 1 },
  { id: "osm",        name: "OpenStreetMap",      color: "#1d6fa4", visible: false, type: "base",      opacity: 1 },
  { id: "aoi",        name: "Area of Interest",   color: "#a78bfa", visible: true,  type: "reference", opacity: 0.8 },
  { id: "image_t1",   name: "Satellite T1",       color: "#64748b", visible: false, type: "analysis",  opacity: 0.85 },
  { id: "image_t2",   name: "Satellite T2",       color: "#94a3b8", visible: false, type: "analysis",  opacity: 0.85 },
  { id: "segmentation_t1", name: "Classification T1", color: "#10b981", visible: false, type: "analysis", opacity: 0.75 },
  { id: "segmentation_t2", name: "Classification T2", color: "#ec4899", visible: false, type: "analysis", opacity: 0.75 },
  { id: "change_mask", name: "U-Net Change Mask",  color: "#38bdf8", visible: false, type: "analysis", opacity: 0.8 },
  { id: "ndvi_change", name: "NDVI Change",        color: "#84cc16", visible: false, type: "analysis",  opacity: 0.75 },
  { id: "ndbi_change", name: "NDBI Change",        color: "#ef4444", visible: false, type: "analysis",  opacity: 0.75 },
  { id: "hotspots", name: "Detected Hotspots", color: "#f87171", visible: false, type: "analysis", opacity: 1 },
];

interface MapState {
  drawnAOI: AOIGeometry | null;
  isDrawingMode: boolean;
  layers: Layer[];
  blinkMode: boolean;
  blinkFrame: "T1" | "T2";
  blinkSpeed: number;
  guidedTourActive: boolean;
  lakeRadarActive: boolean;
  showZones: boolean;
}

/**
 * useMap — manages AOI drawing state, map layers, blink mode,
 * guided tour, lake radar, and zone overlays.
 */
export function useMap() {
  const [state, setState] = useState<MapState>({
    drawnAOI: null,
    isDrawingMode: false,
    layers: INITIAL_LAYERS,
    blinkMode: false,
    blinkFrame: "T1",
    blinkSpeed: 800,
    guidedTourActive: false,
    lakeRadarActive: false,
    showZones: false,
  });

  const blinkIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // --- AOI ---
  const setDrawnAOI = useCallback((aoi: AOIGeometry | null) => {
    setState((prev) => ({ ...prev, drawnAOI: aoi }));
  }, []);

  const setDrawingMode = useCallback((active: boolean) => {
    setState((prev) => ({ ...prev, isDrawingMode: active }));
  }, []);

  const clearAOI = useCallback(() => {
    setState((prev) => ({ ...prev, drawnAOI: null }));
  }, []);

  // --- Layers ---
  const toggleLayer = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      layers: prev.layers.map((l) =>
        l.id === id ? { ...l, visible: !l.visible } : l
      ),
    }));
  }, []);

  const reorderLayers = useCallback((reorderedLayers: Layer[]) => {
    setState((prev) => {
      const nonAnalysis = prev.layers.filter((l) => l.type !== "analysis");
      return { ...prev, layers: [...nonAnalysis, ...reorderedLayers] };
    });
  }, []);

  const setLayerOpacity = useCallback((id: string, opacity: number) => {
    setState((prev) => ({
      ...prev,
      layers: prev.layers.map((l) =>
        l.id === id ? { ...l, opacity } : l
      ),
    }));
  }, []);

  // --- Blink Mode ---
  const toggleBlinkMode = useCallback(() => {
    setState((prev) => {
      const newBlinkMode = !prev.blinkMode;
      if (!newBlinkMode && blinkIntervalRef.current) {
        clearInterval(blinkIntervalRef.current);
        blinkIntervalRef.current = null;
      }
      if (newBlinkMode) {
        blinkIntervalRef.current = setInterval(() => {
          setState((s) => ({
            ...s,
            blinkFrame: s.blinkFrame === "T1" ? "T2" : "T1",
          }));
        }, prev.blinkSpeed);
      }
      return { ...prev, blinkMode: newBlinkMode, blinkFrame: "T1" };
    });
  }, []);

  const setBlinkSpeed = useCallback((speed: number) => {
    setState((prev) => {
      if (blinkIntervalRef.current) {
        clearInterval(blinkIntervalRef.current);
        blinkIntervalRef.current = setInterval(() => {
          setState((s) => ({
            ...s,
            blinkFrame: s.blinkFrame === "T1" ? "T2" : "T1",
          }));
        }, speed);
      }
      return { ...prev, blinkSpeed: speed };
    });
  }, []);

  // --- Guided Tour ---
  const toggleGuidedTour = useCallback(() => {
    setState((prev) => ({ ...prev, guidedTourActive: !prev.guidedTourActive }));
  }, []);

  const stopGuidedTour = useCallback(() => {
    setState((prev) => ({ ...prev, guidedTourActive: false }));
  }, []);

  // --- Lake Radar ---
  const toggleLakeRadar = useCallback(() => {
    setState((prev) => ({ ...prev, lakeRadarActive: !prev.lakeRadarActive }));
  }, []);

  // --- Zones ---
  const toggleZones = useCallback(() => {
    setState((prev) => ({ ...prev, showZones: !prev.showZones }));
  }, []);

  return {
    ...state,
    setDrawnAOI,
    setDrawingMode,
    clearAOI,
    toggleLayer,
    reorderLayers,
    setLayerOpacity,
    toggleBlinkMode,
    setBlinkSpeed,
    toggleGuidedTour,
    stopGuidedTour,
    toggleLakeRadar,
    toggleZones,
  };
}
