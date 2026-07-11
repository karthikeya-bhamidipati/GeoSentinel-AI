"use client";

// =============================================================================
// GeoSentinel AI — MapContainer Component
// Professional GIS map with Leaflet, AOI drawing, HMR boundary enforcement
// =============================================================================

import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from "react";
import type { AOIGeometry } from "@/types";
import { HMR_BOUNDS, HMR_CENTER } from "@/types";
import type { Layer } from "@/hooks/useMap";
import { MapLegend } from "@/components/Map/MapLegend";

export interface MapContainerRef {
  startDrawing: () => void;
  cancelDrawing: () => void;
}

interface MapContainerProps {
  onAOIDrawn: (aoi: AOIGeometry | null) => void;
  onDrawingModeChange: (active: boolean) => void;
  onZoomChange?: (zoom: number) => void;
  drawnAOI: AOIGeometry | null;
  layers?: Layer[];
  result?: any;
}

export const MapContainer = forwardRef<MapContainerRef, MapContainerProps>(({
  onAOIDrawn,
  onDrawingModeChange,
  onZoomChange,
  drawnAOI,
  layers = [],
  result,
}, ref) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null);
  const drawnLayerRef = useRef<any>(null);
  const analysisLayersRef = useRef<Record<string, any>>({});
  const baseLayersRef = useRef<Record<string, any>>({});
  const refLayersRef = useRef<Record<string, any>>({});
  const [isDrawing, setIsDrawing] = useState(false);

  useEffect(() => {
    if (!mapRef.current || leafletMapRef.current) return;

    const init = async () => {
      const L = await import("leaflet");
      // @ts-ignore
      await import("leaflet/dist/leaflet.css");

      const hmrBounds = L.latLngBounds(
        [HMR_BOUNDS.minLat, HMR_BOUNDS.minLng],
        [HMR_BOUNDS.maxLat, HMR_BOUNDS.maxLng]
      );

      const map = L.map(mapRef.current!, {
        center: [HMR_CENTER.lat, HMR_CENTER.lng],
        zoom: 11,
        minZoom: 9,
        maxZoom: 18,
        maxBounds: hmrBounds,
        maxBoundsViscosity: 0.9,
        zoomControl: false,
        attributionControl: true,
      });

      // Zoom control — top right
      L.control.zoom({ position: "topright" }).addTo(map);

      // Scale control — bottom right
      L.control.scale({ position: "bottomright", imperial: false }).addTo(map);

      // --- Base layers ---
      const satelliteLayer = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: "Tiles © Esri — Esri, i-cubed, USDA, USGS, AEX, GeoEye",
          maxZoom: 18,
        }
      ).addTo(map);

      const osmLayer = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }
      );

      baseLayersRef.current["satellite"] = satelliteLayer;
      baseLayersRef.current["osm"] = osmLayer;

      // --- HMR dim overlay (darken outside boundary) ---
      const outerBounds: [number, number][] = [
        [-85, -180], [85, -180], [85, 180], [-85, 180], [-85, -180],
      ];
      const innerBounds: [number, number][] = [
        [HMR_BOUNDS.minLat, HMR_BOUNDS.minLng],
        [HMR_BOUNDS.minLat, HMR_BOUNDS.maxLng],
        [HMR_BOUNDS.maxLat, HMR_BOUNDS.maxLng],
        [HMR_BOUNDS.maxLat, HMR_BOUNDS.minLng],
        [HMR_BOUNDS.minLat, HMR_BOUNDS.minLng],
      ];
      const dimOverlay = L.polygon([outerBounds, innerBounds], {
        color: "transparent",
        fillColor: "#000000",
        fillOpacity: 0.35,
        interactive: false,
      });

      // --- HMR boundary ring ---
      const hmrRing = L.rectangle(hmrBounds, {
        color: "#1d6fa4",
        weight: 2,
        fill: false,
        dashArray: "6, 4",
        interactive: false,
        opacity: 0.8,
      });

      // --- HMR label ---
      const center = hmrBounds.getCenter();
      const hmrLabel = L.marker([HMR_BOUNDS.maxLat - 0.02, center.lng], {
        icon: L.divIcon({
          html: `<div style="background:rgba(29,111,164,0.85);color:#fff;padding:2px 8px;border-radius:3px;font-size:10px;font-family:Inter,sans-serif;font-weight:600;white-space:nowrap;letter-spacing:0.06em;pointer-events:none;">HYDERABAD METROPOLITAN REGION</div>`,
          className: "",
          iconAnchor: [80, 0],
        }),
        interactive: false,
      });

      const hmrGroup = L.featureGroup([dimOverlay, hmrRing, hmrLabel]).addTo(map);
      refLayersRef.current["hmr_boundary"] = hmrGroup;

      // --- Drawn items layer ---
      const drawnItems = new L.FeatureGroup();
      map.addLayer(drawnItems);
      drawnLayerRef.current = drawnItems;

      // --- Zoom change callback ---
      map.on("zoom", () => {
        onZoomChange?.(map.getZoom());
      });
      onZoomChange?.(map.getZoom());

      // --- Broadcast coordinates to status bar ---
      map.on("mousemove", (e: any) => {
        window.dispatchEvent(
          new CustomEvent("map:mousemove", {
            detail: { lat: e.latlng.lat, lng: e.latlng.lng },
          })
        );
      });

      leafletMapRef.current = map;
    };

    init().catch(console.error);

    return () => {
      leafletMapRef.current?.remove();
      leafletMapRef.current = null;
    };
  }, []);

  // Sync drawn AOI state with map layer
  useEffect(() => {
    if (!drawnLayerRef.current || !leafletMapRef.current) return;
    
    // Always clear existing drawing first to ensure it updates when a new history record is selected
    drawnLayerRef.current.clearLayers();
    
    if (drawnAOI) {
      import("leaflet").then(L => {
        // Redraw based on state
        const coords = drawnAOI.coordinates[0] as number[][];
        const lats = coords.map((c) => c[1]);
        const lngs = coords.map((c) => c[0]);
        const bounds = L.latLngBounds(
          [Math.min(...lats), Math.min(...lngs)],
          [Math.max(...lats), Math.max(...lngs)]
        );
        
        const rect = L.rectangle(bounds, {
          color: "#e67e22",
          weight: 2.5,
          fillColor: "#e67e22",
          fillOpacity: 0.12,
          dashArray: undefined,
        });
        
        if (drawnLayerRef.current && leafletMapRef.current) {
          drawnLayerRef.current.addLayer(rect);
          leafletMapRef.current.fitBounds(bounds, { padding: [50, 50] });
        }
      });
    }
  }, [drawnAOI]);

  // Manage analysis overlays based on layers state and result
  useEffect(() => {
    if (!leafletMapRef.current) return;
    
    const initOverlays = async () => {
      const L = await import("leaflet");
      const map = leafletMapRef.current;
      
      const layerIdToOutputKey: Record<string, string> = {
        "image_t1": "image_t1_png",
        "image_t2": "image_t2_png",
        "segmentation_t1": "mask_t1_png",
        "segmentation_t2": "mask_t2_png",
        "ndvi_change": "ndvi_delta_png",
        "ndbi_change": "ndbi_delta_png",
      };

      layers.forEach((layer) => {
        if (layer.type === "base") {
          const l = baseLayersRef.current[layer.id];
          if (l) {
            if (layer.visible && !map.hasLayer(l)) {
              map.addLayer(l);
            } else if (!layer.visible && map.hasLayer(l)) {
              map.removeLayer(l);
            }
          }
        } else if (layer.type === "reference") {
          if (layer.id === "hmr_boundary") {
            const l = refLayersRef.current["hmr_boundary"];
            if (l) {
               if (layer.visible && !map.hasLayer(l)) {
                 map.addLayer(l);
               } else if (!layer.visible && map.hasLayer(l)) {
                 map.removeLayer(l);
               }
            }
          } else if (layer.id === "aoi") {
             if (drawnLayerRef.current) {
                 if (layer.visible && !map.hasLayer(drawnLayerRef.current)) {
                     map.addLayer(drawnLayerRef.current);
                 } else if (!layer.visible && map.hasLayer(drawnLayerRef.current)) {
                     map.removeLayer(drawnLayerRef.current);
                 }
             }
          }
        } else if (layer.type === "analysis") {
          const outputKey = layerIdToOutputKey[layer.id];
          const fileUrl = result?.outputs?.[outputKey];
          
          // If layer should be visible and we have a URL + bounds
          if (layer.visible && fileUrl && drawnAOI) {
            if (!analysisLayersRef.current[layer.id]) {
              // Calculate bounds from drawnAOI
              const coords = drawnAOI.coordinates[0] as number[][];
              const lats = coords.map((c) => c[1]);
              const lngs = coords.map((c) => c[0]);
              const bounds = L.latLngBounds(
                [Math.min(...lats), Math.min(...lngs)],
                [Math.max(...lats), Math.max(...lngs)]
              );

              const apiBase = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/v1";
              const imageUrl = `${apiBase}/download/${result.job_id}/${outputKey}`;

              const imageOverlay = L.imageOverlay(imageUrl, bounds, {
                opacity: 0.8,
                interactive: true,
              }).addTo(map);

              analysisLayersRef.current[layer.id] = imageOverlay;
            }
          } else {
            // If layer should be hidden or we lack data, remove it if it exists
            if (analysisLayersRef.current[layer.id]) {
              map.removeLayer(analysisLayersRef.current[layer.id]);
              delete analysisLayersRef.current[layer.id];
            }
          }
        }
      });
    };
    
    initOverlays();
  }, [layers, result, drawnAOI]);

  const handleDrawRectangle = async () => {
    if (!leafletMapRef.current) return;

    const L = await import("leaflet");

    drawnLayerRef.current?.clearLayers();

    setIsDrawing(true);
    onDrawingModeChange(true);

    const map = leafletMapRef.current;
    map.dragging.disable();
    if (mapRef.current) mapRef.current.style.cursor = "crosshair";

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
      if (rectangleLayer) drawnLayerRef.current.removeLayer(rectangleLayer);

      const bounds = L.latLngBounds(startLatLng, e.latlng);
      rectangleLayer = L.rectangle(bounds, {
        color: "#e67e22",
        weight: 2,
        fillColor: "#e67e22",
        fillOpacity: 0.15,
        dashArray: "5, 5",
      });
      drawnLayerRef.current.addLayer(rectangleLayer);
    };

    const onMouseUp = (e: any) => {
      map.off("mousemove", onMouseMove);
      map.off("mouseup", onMouseUp);
      map.dragging.enable();
      if (mapRef.current) mapRef.current.style.cursor = "";

      if (!startLatLng || !rectangleLayer) {
        setIsDrawing(false);
        onDrawingModeChange(false);
        return;
      }

      const bounds = L.latLngBounds(startLatLng, e.latlng);
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();

      if (Math.abs(sw.lat - ne.lat) < 0.001 || Math.abs(sw.lng - ne.lng) < 0.001) {
        drawnLayerRef.current.removeLayer(rectangleLayer);
        setIsDrawing(false);
        onDrawingModeChange(false);
        return;
      }

      // Final style for drawn AOI
      rectangleLayer.setStyle({
        color: "#e67e22",
        weight: 2.5,
        fillColor: "#e67e22",
        fillOpacity: 0.12,
        dashArray: undefined,
      });

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

    const cancelDrawing = () => {
      map.off("mousedown", onMouseDown);
      map.off("mousemove", onMouseMove);
      map.off("mouseup", onMouseUp);
      map.dragging.enable();
      if (mapRef.current) mapRef.current.style.cursor = "";
      if (rectangleLayer) drawnLayerRef.current.removeLayer(rectangleLayer);
      
      setIsDrawing(false);
      onDrawingModeChange(false);
      document.removeEventListener("keydown", onKeyDown);
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        cancelDrawing();
      }
    };

    document.addEventListener("keydown", onKeyDown);

    map.on("mousedown", onMouseDown);
  };

  useImperativeHandle(ref, () => ({
    startDrawing: handleDrawRectangle,
    cancelDrawing: () => {
      // Internal cancel logic is already bound to escape, but we can trigger it
      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      document.dispatchEvent(event);
    }
  }));

  // Allow MapContainer to turn off drawing from external trigger
  useEffect(() => {
    // If the external drawing mode is toggled while we are drawing, we don't have a direct way to cancel
    // unless we extract cancelDrawing. For simplicity, we just rely on Escape and MapToolbar clicks.
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {/* Map Canvas */}
      <div ref={mapRef} style={{ width: "100%", height: "100%" }} id="map-canvas" />

      {/* Dynamic Floating Legend */}
      <MapLegend layers={layers} />

      {/* Drawing instruction tooltip */}
      {isDrawing && (
        <div
          style={{
            position: "absolute",
            top: "var(--space-3)",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 500,
            background: "var(--color-surface)",
            border: "1px solid var(--color-primary-border)",
            borderRadius: "var(--radius-sm)",
            padding: "6px 14px",
            fontSize: "var(--font-size-sm)",
            fontWeight: 500,
            color: "var(--color-primary)",
            boxShadow: "var(--shadow-sm)",
            pointerEvents: "none",
            whiteSpace: "nowrap",
          }}
        >
          Click and drag to define your Area of Interest
        </div>
      )}

      {/* Map Toolbar (Restored) */}
      <div
        style={{
          position: "absolute",
          top: "80px",
          right: "12px",
          zIndex: 400,
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        <button
          id="map-tool-draw-rect"
          type="button"
          onMouseDown={(e) => e.stopPropagation()}
          onMouseUp={(e) => e.stopPropagation()}
          onClick={(e) => {
            e.stopPropagation();
            if (isDrawing) {
              const event = new KeyboardEvent('keydown', { key: 'Escape' });
              document.dispatchEvent(event);
            } else {
              handleDrawRectangle();
            }
          }}
          style={{
            width: "36px",
            height: "36px",
            background: isDrawing ? "var(--color-accent)" : "var(--color-surface)",
            color: isDrawing ? "#fff" : "var(--color-text)",
            border: "1px solid var(--color-border)",
            borderRadius: "4px",
            boxShadow: "var(--shadow-sm)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
          title={isDrawing ? "Cancel Drawing" : "Draw Area of Interest"}
        >
          {isDrawing ? "❌" : "📐"}
        </button>
      </div>
    </div>
  );
});
