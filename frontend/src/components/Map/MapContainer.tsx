"use client";

import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { HMR_CENTER, HMR_BOUNDS, AOIGeometry, AnalysisResult } from "@/types";
import { Layer } from "@/hooks/useMap";
import { IT_CORRIDOR_ZONE, OLD_CITY_ZONE } from "@/data/hyderabad-zones";
import { Crosshair } from "lucide-react";
import { useRasterHover, CLASS_COLORS } from "@/hooks/useRasterHover";

export interface MapContainerRef {
  flyTo: (center: [number, number], zoom: number) => void;
}

interface MapContainerProps {
  onAOIDrawn: (aoi: AOIGeometry | null) => void;
  onDrawingModeChange: (isDrawing: boolean) => void;
  onZoomChange: (zoom: number) => void;
  drawnAOI: AOIGeometry | null;
  layers: Layer[];
  result: AnalysisResult | null;
  blinkMode: boolean;
  blinkFrame: "T1" | "T2";
  lakeRadarActive: boolean;
  showZones: boolean;
}

export const MapContainer = forwardRef<MapContainerRef, MapContainerProps>(({
  onAOIDrawn,
  onDrawingModeChange,
  onZoomChange,
  drawnAOI,
  layers,
  result,
  blinkMode,
  blinkFrame,
  lakeRadarActive,
  showZones
}, ref) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [isDrawingUI, setIsDrawingUI] = useState(false);
  const [hotspotHover, setHotspotHover] = useState<{x: number, y: number, props: any} | null>(null);

  // Pass map instance only after it's loaded (mapLoaded triggers re-render)
  const rasterHover = useRasterHover(mapLoaded ? mapRef.current : null, result, layers);

  useEffect(() => {
    const handler = (e: any) => setHotspotHover(e.detail);
    window.addEventListener('map:hotspotHover', handler);
    return () => window.removeEventListener('map:hotspotHover', handler);
  }, []);

  const drawState = useRef<{
    active: boolean;
    startPoint: [number, number] | null;
    currentPoint: [number, number] | null;
  }>({ active: false, startPoint: null, currentPoint: null });

  useImperativeHandle(ref, () => ({
    flyTo: (center: [number, number], zoom: number) => {
      if (mapRef.current) {
        mapRef.current.flyTo({ center, zoom, speed: 1.2, curve: 1.42 });
      }
    }
  }));

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          'dark-base': { type: 'raster', tiles: ['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'], tileSize: 256 },
          'osm-base': { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256 },
          'satellite-base': { type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize: 256 }
        },
        layers: [
          { id: 'dark-base-layer', type: 'raster', source: 'dark-base', minzoom: 0, maxzoom: 22, layout: { visibility: 'visible' } },
          { id: 'osm-base-layer', type: 'raster', source: 'osm-base', minzoom: 0, maxzoom: 22, layout: { visibility: 'none' } },
          { id: 'satellite-base-layer', type: 'raster', source: 'satellite-base', minzoom: 0, maxzoom: 22, layout: { visibility: 'none' } }
        ]
      },
      center: [HMR_CENTER.lng, HMR_CENTER.lat],
      zoom: 11,
      minZoom: 8,
      maxBounds: [[76.5, 15.5], [80.5, 19.5]], // ~150km Buffer around Hyderabad
      pitch: 0,
      bearing: 0,
      attributionControl: false
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-left');

    map.on('load', () => {
      setMapLoaded(true);
      mapRef.current = map;

      // Setup Zones
      map.addSource('zones', { type: 'geojson', data: { type: 'FeatureCollection', features: [IT_CORRIDOR_ZONE, OLD_CITY_ZONE] }});
      map.addLayer({ id: 'zones-fill', type: 'fill', source: 'zones', paint: { 'fill-color': ['get', 'color'], 'fill-opacity': 0.2 }, layout: { visibility: 'none' }});
      map.addLayer({ id: 'zones-line', type: 'line', source: 'zones', paint: { 'line-color': ['get', 'color'], 'line-width': 2 }, layout: { visibility: 'none' }});

      // Setup Native AOI Draw Layer
      map.addSource('custom-aoi-draw', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({ id: 'custom-aoi-fill', type: 'fill', source: 'custom-aoi-draw', paint: { 'fill-color': '#a78bfa', 'fill-opacity': 0.1 } });
      map.addLayer({ id: 'custom-aoi-glow', type: 'line', source: 'custom-aoi-draw', paint: { 'line-color': '#a78bfa', 'line-width': 8, 'line-blur': 5, 'line-opacity': 0.5 } });
      map.addLayer({ id: 'custom-aoi-line', type: 'line', source: 'custom-aoi-draw', paint: { 'line-color': '#a78bfa', 'line-width': 2 } });
    });

    map.on('zoom', () => { onZoomChange(map.getZoom()); });

    const handleFlyTo = (e: Event) => {
      const customEvent = e as CustomEvent;
      console.log("MapContainer received map:flyTo event", customEvent.detail);
      if (customEvent.detail) {
        map.flyTo({ 
          center: customEvent.detail.center, 
          zoom: customEvent.detail.zoom, 
          speed: 1.2, 
          curve: 1.42 
        });
        console.log("map.flyTo executed!");
      }
    };
    window.addEventListener('map:flyTo', handleFlyTo);

    // Native Drawing Interaction Logic
    map.on('click', (e) => {
      if (!drawState.current.active) return;
      const pt: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      
      if (!drawState.current.startPoint) {
        drawState.current.startPoint = pt;
        drawState.current.currentPoint = pt;
      } else {
        const p1 = drawState.current.startPoint;
        const p2 = pt;
        const polygon: AOIGeometry = {
          type: "Polygon",
          coordinates: [[[p1[0], p1[1]], [p2[0], p1[1]], [p2[0], p2[1]], [p1[0], p2[1]], [p1[0], p1[1]]]]
        };
        drawState.current.active = false;
        drawState.current.startPoint = null;
        drawState.current.currentPoint = null;
        setIsDrawingUI(false);
        onDrawingModeChange(false);
        onAOIDrawn(polygon);
        map.getCanvas().style.cursor = '';
      }
    });

    map.on('mousemove', (e) => {
      window.dispatchEvent(new CustomEvent('map:mousemove', { detail: { lat: e.lngLat.lat, lng: e.lngLat.lng } }));

      if (!drawState.current.active || !drawState.current.startPoint) return;
      drawState.current.currentPoint = [e.lngLat.lng, e.lngLat.lat];
      const p1 = drawState.current.startPoint;
      const p2 = drawState.current.currentPoint;
      const polygon: AOIGeometry = {
        type: "Polygon",
        coordinates: [[[p1[0], p1[1]], [p2[0], p1[1]], [p2[0], p2[1]], [p1[0], p2[1]], [p1[0], p1[1]]]]
      };
      const source = map.getSource('custom-aoi-draw') as maplibregl.GeoJSONSource;
      if (source) source.setData({ type: 'Feature', geometry: polygon as any, properties: {} });
    });

    return () => {
      window.removeEventListener('map:flyTo', handleFlyTo);
      map.remove();
    };
  }, [onZoomChange, onAOIDrawn, onDrawingModeChange]);

  // Handle Drawn AOI sync (from parent)
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const source = mapRef.current.getSource('custom-aoi-draw') as maplibregl.GeoJSONSource;
    if (source) {
      if (drawnAOI) {
        source.setData({ type: 'Feature', geometry: drawnAOI as any, properties: {} });
      } else if (!drawState.current.active) {
        // If not actively drawing and drawnAOI is null, clear it
        source.setData({ type: 'FeatureCollection', features: [] });
      }
    }
  }, [drawnAOI, mapLoaded]);

  // Handle Layer Visibility & Opacity
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    // Sync Base Maps
    const isDarkVisible = layers.find(l => l.id === "dark")?.visible ?? true;
    const isOsmVisible = layers.find(l => l.id === "osm")?.visible ?? false;
    const isSatelliteVisible = layers.find(l => l.id === "satellite")?.visible ?? false;
    
    if (map.getLayer('dark-base-layer')) map.setLayoutProperty('dark-base-layer', 'visibility', isDarkVisible ? 'visible' : 'none');
    if (map.getLayer('osm-base-layer')) map.setLayoutProperty('osm-base-layer', 'visibility', isOsmVisible ? 'visible' : 'none');
    if (map.getLayer('satellite-base-layer')) map.setLayoutProperty('satellite-base-layer', 'visibility', isSatelliteVisible ? 'visible' : 'none');

    // Sync Reference Layers (AOI)
    const isAoiVisible = layers.find(l => l.id === "aoi")?.visible ?? true;
    if (map.getLayer('custom-aoi-fill')) map.setLayoutProperty('custom-aoi-fill', 'visibility', isAoiVisible ? 'visible' : 'none');
    if (map.getLayer('custom-aoi-glow')) map.setLayoutProperty('custom-aoi-glow', 'visibility', isAoiVisible ? 'visible' : 'none');
    if (map.getLayer('custom-aoi-line')) map.setLayoutProperty('custom-aoi-line', 'visibility', isAoiVisible ? 'visible' : 'none');

    // Custom Raster Sources for Results
    const apiBase = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/v1";
    
    layers.forEach(layer => {
      if (layer.type === "analysis" && result) {
        const sourceId = `source-${layer.id}`;
        const layerId = `layer-${layer.id}`;
        let fileType = "";
        
        if (layer.id === "hotspots") {
          const sourceId = `source-hotspots`;
          const layerIdGlow = `layer-hotspots-glow`;
          const layerIdCore = `layer-hotspots-core`;
          
          const hotspotsData = (result.temporal_stats?.segmentation_change as any)?.hotspots || [];
          console.log(`Hotspots layer: ${hotspotsData.length} hotspots found`, hotspotsData);
          
          // Filter out hotspots with missing coordinates
          const validHotspots = hotspotsData.filter((h: any) => h.center_lat != null && h.center_lon != null);
          
          const features = validHotspots.map((h: any) => ({
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [h.center_lon, h.center_lat]
            },
            properties: {
              area: h.area_pixels,
              transition: `${h.from_class} → ${h.to_class}`
            }
          }));
          
          const geojson = {
            type: "FeatureCollection",
            features: features
          };
          
          const existingSource = map.getSource(sourceId) as maplibregl.GeoJSONSource;
          if (!existingSource) {
            map.addSource(sourceId, { type: 'geojson', data: geojson as any });
            
            map.addLayer({
              id: layerIdGlow,
              type: 'circle',
              source: sourceId,
              paint: {
                'circle-color': '#f87171',
                'circle-radius': ['+', 10, ['min', 40, ['/', ['get', 'area'], 50]]], // scale by area
                'circle-blur': 1,
                'circle-opacity': 0.6
              },
              layout: { visibility: 'none' }
            });
            
            map.addLayer({
              id: layerIdCore,
              type: 'circle',
              source: sourceId,
              paint: {
                'circle-color': '#f87171',
                'circle-radius': 4,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#fff'
              },
              layout: { visibility: 'none' }
            });
            
            // Interaction
            map.on('mouseenter', layerIdCore, (e) => {
               map.getCanvas().style.cursor = 'pointer';
               if (e.features && e.features[0]) {
                 window.dispatchEvent(new CustomEvent('map:hotspotHover', { detail: { x: e.point.x, y: e.point.y, props: e.features[0].properties } }));
               }
            });
            map.on('mouseleave', layerIdCore, () => {
               map.getCanvas().style.cursor = '';
               window.dispatchEvent(new CustomEvent('map:hotspotHover', { detail: null }));
            });
            map.on('mousemove', layerIdCore, (e) => {
               if (e.features && e.features[0]) {
                 window.dispatchEvent(new CustomEvent('map:hotspotHover', { detail: { x: e.point.x, y: e.point.y, props: e.features[0].properties } }));
               }
            });
          } else {
             existingSource.setData(geojson as any);
          }
          
          map.setLayoutProperty(layerIdGlow, 'visibility', layer.visible ? 'visible' : 'none');
          map.setLayoutProperty(layerIdCore, 'visibility', layer.visible ? 'visible' : 'none');
          
          return; // Skip raster logic
        }

        if (layer.id === "image_t1") fileType = "image_t1_png";
        else if (layer.id === "image_t2") fileType = "image_t2_png";
        else if (layer.id === "segmentation_t1") fileType = "mask_t1_png";
        else if (layer.id === "segmentation_t2") fileType = "mask_t2_png";
        else if (layer.id === "change_mask") fileType = "change_mask_png";
        else if (layer.id === "ndvi_change") fileType = "ndvi_delta_png";
        else if (layer.id === "ndbi_change") fileType = "ndbi_delta_png";

        if (fileType && result.outputs && result.outputs[fileType as keyof typeof result.outputs]) {
          const bbox = result.metadata?.bbox || [76.5, 15.5, 80.5, 19.5]; // Fallback bounds
          const coordinates = [
            [bbox[0], bbox[3]], // top-left
            [bbox[2], bbox[3]], // top-right
            [bbox[2], bbox[1]], // bottom-right
            [bbox[0], bbox[1]]  // bottom-left
          ];
          const newUrl = `${apiBase}/download/${result.job_id}/${fileType}`;

          const existingSource = map.getSource(sourceId) as any;
          const currentUrl = existingSource ? (existingSource._currentUrl || existingSource.url) : null;
          
          if (!existingSource || currentUrl !== newUrl) {
            if (map.getLayer(layerId)) map.removeLayer(layerId);
            if (existingSource) map.removeSource(sourceId);
            
            map.addSource(sourceId, {
              type: 'image',
              url: newUrl,
              coordinates: coordinates as any
            });
            
            map.addLayer({
              id: layerId,
              type: 'raster',
              source: sourceId,
              paint: {
                'raster-opacity': layer.opacity ?? 0.8,
                'raster-resampling': 'nearest'
              },
              layout: { visibility: 'none' }
            });
            (map.getSource(sourceId) as any)._currentUrl = newUrl;
          }
          
          // Update visibility and opacity
          let isVis = layer.visible;
          if (blinkMode && (layer.id === "image_t1" || layer.id === "segmentation_t1")) {
            isVis = blinkFrame === "T1";
          }
          if (blinkMode && (layer.id === "image_t2" || layer.id === "segmentation_t2")) {
            isVis = blinkFrame === "T2";
          }

          map.setLayoutProperty(layerId, 'visibility', isVis ? 'visible' : 'none');
          map.setPaintProperty(layerId, 'raster-opacity', layer.opacity ?? 0.8);
        } else if (result.outputs && !result.outputs[fileType as keyof typeof result.outputs]) {
          // If file is not available for this job, hide the layer if it exists
          if (map.getLayer(layerId)) {
            map.setLayoutProperty(layerId, 'visibility', 'none');
          }
        }
      }
    });

  }, [layers, mapLoaded, result, blinkMode, blinkFrame]);

  // Handle Zones Visibility
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;
    if (map.getLayer('zones-fill')) {
      map.setLayoutProperty('zones-fill', 'visibility', showZones ? 'visible' : 'none');
      map.setLayoutProperty('zones-line', 'visibility', showZones ? 'visible' : 'none');
    }
  }, [showZones, mapLoaded]);

  const handleDrawRect = () => {
    if (mapRef.current) {
      const isCurrentlyDrawing = drawState.current.active;
      
      if (isCurrentlyDrawing) {
        // Cancel drawing mode
        drawState.current.active = false;
        drawState.current.startPoint = null;
        drawState.current.currentPoint = null;
        setIsDrawingUI(false);
        onDrawingModeChange(false);
        mapRef.current.getCanvas().style.cursor = '';
      } else {
        // Start drawing mode
        drawState.current.active = true;
        drawState.current.startPoint = null;
        drawState.current.currentPoint = null;
        setIsDrawingUI(true);
        onDrawingModeChange(true);
        mapRef.current.getCanvas().style.cursor = 'crosshair';
        
        // Clear current source
        const source = mapRef.current.getSource('custom-aoi-draw') as maplibregl.GeoJSONSource;
        if (source) source.setData({ type: 'FeatureCollection', features: [] });
        onAOIDrawn(null);
      }
    }
  };

  return (
    <div style={{ position: "absolute", inset: 0, background: "var(--color-bg)" }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%', outline: 'none' }} />
      
      {hotspotHover && (
        <div style={{
          position: 'absolute',
          left: hotspotHover.x + 15,
          top: hotspotHover.y + 15,
          background: 'var(--color-surface-glass)',
          backdropFilter: 'blur(12px)',
          border: '1px solid var(--color-border)',
          padding: '8px 12px',
          borderRadius: '6px',
          pointerEvents: 'none',
          zIndex: 1000,
          boxShadow: 'var(--shadow-lg)',
          minWidth: '150px'
        }}>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)', marginBottom: '4px' }}>Change Hotspot</div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Transition:</span>
            <span style={{ color: 'var(--color-text)' }}>{hotspotHover.props.transition}</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Area:</span>
            <span style={{ color: 'var(--color-text)' }}>{hotspotHover.props.area} px</span>
          </div>
        </div>
      )}

      {rasterHover && !hotspotHover && (
        <div style={{
          position: 'absolute',
          left: rasterHover.x + 15,
          top: rasterHover.y + 15,
          background: 'var(--color-surface-glass)',
          backdropFilter: 'blur(12px)',
          border: `1px solid ${
            CLASS_COLORS.find(c => c.name === rasterHover.className)?.rgb 
              ? `rgba(${CLASS_COLORS.find(c => c.name === rasterHover.className)?.rgb.join(',')}, 0.5)`
              : 'var(--color-border)'
          }`,
          padding: '8px 12px',
          borderRadius: '6px',
          pointerEvents: 'none',
          zIndex: 999,
          boxShadow: 'var(--shadow-lg)',
          minWidth: '130px'
        }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Classification {rasterHover.date}
          </div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ 
              width: '10px', height: '10px', borderRadius: '50%', 
              backgroundColor: `rgb(${CLASS_COLORS.find(c => c.name === rasterHover.className)?.rgb.join(',')})`
            }}></span>
            {rasterHover.className}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Total Area:</span>
            <span style={{ color: 'var(--color-text)', fontWeight: 500 }}>{rasterHover.area} km²</span>
          </div>
        </div>
      )}

      {/* Map Toolbar */}
      <div className="map-toolbar">
        <button 
          id="map-tool-draw-rect"
          onClick={handleDrawRect}
          className="map-toolbar-btn"
          style={{
            background: isDrawingUI ? "var(--color-primary)" : "var(--color-surface-glass)",
            color: isDrawingUI ? "#000" : "var(--color-text)",
          }}
          title={isDrawingUI ? "Click & Drag to Draw Bounding Box" : "Draw AOI Bounding Box"}
        >
          <Crosshair size={20} />
        </button>
      </div>

      {lakeRadarActive && (
        <div style={{
          position: "absolute",
          top: "50%", left: "50%", transform: "translate(-50%, -50%)",
          zIndex: 5, pointerEvents: "none",
          width: "300px", height: "300px",
          border: "2px solid rgba(16, 185, 129, 0.5)",
          borderRadius: "50%",
          boxShadow: "inset 0 0 50px rgba(16, 185, 129, 0.1)",
          display: "flex", alignItems: "center", justifyContent: "center"
        }}>
          <div style={{
            position: "absolute", width: "100%", height: "100%",
            background: "conic-gradient(from 0deg, transparent 0deg, transparent 270deg, rgba(16, 185, 129, 0.2) 360deg)",
            borderRadius: "50%",
            animation: "radar-spin 2s linear infinite"
          }} />
          <style dangerouslySetInnerHTML={{__html: `
            @keyframes radar-spin { 100% { transform: rotate(360deg); } }
          `}} />
        </div>
      )}
    </div>
  );
});

MapContainer.displayName = "MapContainer";
