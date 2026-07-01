"use client";

// =============================================================================
// GeoSentinel AI — useMap Hook
// =============================================================================

import { useState, useCallback } from "react";
import type { AOIGeometry, LatLng } from "@/types";

interface MapState {
  drawnAOI: AOIGeometry | null;
  isDrawingMode: boolean;
}

/**
 * useMap — manages AOI drawing state.
 *
 * Tracks the user-drawn polygon and drawing mode activation.
 * The actual drawing is performed by Leaflet.draw on the map.
 */
export function useMap() {
  const [state, setState] = useState<MapState>({
    drawnAOI: null,
    isDrawingMode: false,
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

  return {
    ...state,
    setDrawnAOI,
    setDrawingMode,
    clearAOI,
  };
}
