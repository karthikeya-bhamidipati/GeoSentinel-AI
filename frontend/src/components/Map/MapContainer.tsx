"use client";

// =============================================================================
// GeoSentinel AI — MapContainer Component
// =============================================================================

import { useEffect, useRef, useState } from "react";
import type { AOIGeometry } from "@/types";
import { HMR_BOUNDS, HMR_CENTER } from "@/types";

interface MapContainerProps {
  onAOIDrawn: (aoi: AOIGeometry | null) => void;
  onDrawingModeChange: (active: boolean) => void;
  drawnAOI: AOIGeometry | null;
}

export function MapContainer({
  onAOIDrawn,
  onDrawingModeChange,
  drawnAOI,
}: MapContainerProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null);
  const drawnLayerRef = useRef<any>(null);
  const [isDrawing, setIsDrawing] = useState(false);

  useEffect(() => {
    if (!mapRef.current || leafletMapRef.current) return;

    // Dynamic import to prevent SSR
    const init = async () => {
      const L = await import("leaflet");
      // @ts-ignore
      await import("leaflet/dist/leaflet.css");

      const map = L.map(mapRef.current!, {
        center: [HMR_CENTER.lat, HMR_CENTER.lng],
        zoom: 10,
        zoomControl: true,
        attributionControl: true,
      });

      // Dark satellite base layer
      L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
          attribution:
            "Tiles © Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP",
          maxZoom: 18,
        }
      ).addTo(map);

      // Labels overlay
      L.tileLayer(
        "https://stamen-tiles-{s}.a.ssl.fastly.net/toner-labels/{z}/{x}/{y}{r}.png",
        {
          attribution:
            'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
          opacity: 0.5,
        }
      ).addTo(map);

      // HMR boundary (restrict drawing to this area)
      const hmrBounds = L.latLngBounds(
        [HMR_BOUNDS.minLat, HMR_BOUNDS.minLng],
        [HMR_BOUNDS.maxLat, HMR_BOUNDS.maxLng]
      );

      // Dim overlay outside HMR
      const outerBounds: [number, number][] = [
        [-90, -180],
        [90, -180],
        [90, 180],
        [-90, 180],
        [-90, -180],
      ];

      const innerBounds: [number, number][] = [
        [HMR_BOUNDS.minLat, HMR_BOUNDS.minLng],
        [HMR_BOUNDS.minLat, HMR_BOUNDS.maxLng],
        [HMR_BOUNDS.maxLat, HMR_BOUNDS.maxLng],
        [HMR_BOUNDS.maxLat, HMR_BOUNDS.minLng],
        [HMR_BOUNDS.minLat, HMR_BOUNDS.minLng],
      ];

      L.polygon([outerBounds, innerBounds], {
        color: "transparent",
        fillColor: "#000000",
        fillOpacity: 0.5,
        interactive: false,
      }).addTo(map);

      // HMR boundary ring
      L.rectangle(hmrBounds, {
        color: "#0ea5e9",
        weight: 2,
        fill: false,
        dashArray: "6, 4",
        interactive: false,
      }).addTo(map);

      const drawnItems = new L.FeatureGroup();
      map.addLayer(drawnItems);
      drawnLayerRef.current = drawnItems;

      leafletMapRef.current = map;
    };

    init().catch(console.error);

    return () => {
      leafletMapRef.current?.remove();
      leafletMapRef.current = null;
    };
  }, []);

  // Clear drawn AOI when drawnAOI becomes null
  useEffect(() => {
    if (!drawnAOI && drawnLayerRef.current) {
      drawnLayerRef.current.clearLayers();
    }
  }, [drawnAOI]);

  const handleDrawRectangle = async () => {
    if (!leafletMapRef.current) return;

    const L = await import("leaflet");

    // Remove existing drawing
    drawnLayerRef.current?.clearLayers();

    setIsDrawing(true);
    onDrawingModeChange(true);

    const map = leafletMapRef.current;

    // Simple click-drag rectangle drawing
    let startLatLng: any = null;
    let rectangleLayer: any = null;

    const onMouseDown = (e: any) => {
      startLatLng = e.latlng;

      map.off("mousedown", onMouseDown);
      map.on("mousemove", onMouseMove);
      map.on("mouseup", onMouseUp);
    };

    const onMouseMove = (e: any) => {
      if (!startLatLng) return;

      if (rectangleLayer) {
        drawnLayerRef.current.removeLayer(rectangleLayer);
      }

      const bounds = L.latLngBounds(startLatLng, e.latlng);
      rectangleLayer = L.rectangle(bounds, {
        color: "#0ea5e9",
        weight: 2,
        fillColor: "#0ea5e9",
        fillOpacity: 0.1,
      });
      drawnLayerRef.current.addLayer(rectangleLayer);
    };

    const onMouseUp = (e: any) => {
      map.off("mousemove", onMouseMove);
      map.off("mouseup", onMouseUp);

      if (!startLatLng) return;

      const bounds = L.latLngBounds(startLatLng, e.latlng);
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();

      const aoi: AOIGeometry = {
        type: "Polygon",
        coordinates: [[
          [sw.lng, sw.lat],
          [ne.lng, sw.lat],
          [ne.lng, ne.lat],
          [sw.lng, ne.lat],
          [sw.lng, sw.lat],
        ]],
      };

      onAOIDrawn(aoi);
      setIsDrawing(false);
      onDrawingModeChange(false);
    };

    map.on("mousedown", onMouseDown);
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div ref={mapRef} style={{ width: "100%", height: "100%" }} />

      {/* Draw AOI Button */}
      <button
        onClick={handleDrawRectangle}
        className={`btn btn-sm ${isDrawing ? "btn-primary" : "btn-ghost"}`}
        style={{
          position: "absolute",
          top: "12px",
          left: "12px",
          zIndex: 500,
        }}
      >
        ✏️ {isDrawing ? "Click & drag to draw AOI" : "Draw AOI"}
      </button>
    </div>
  );
}
