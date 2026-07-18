"use client";

// =============================================================================
// GeoSentinel AI — Main Page (v2.0)
// Dark holographic command center layout with CyberTerminal,
// DataCardStack, GuidedTour, BlinkMode, NLPChatBox, and Toasts
// =============================================================================

import { useState, useRef, useCallback } from "react";
import { useToast } from "@/hooks/useToast";
import { ToastContainer } from "@/components/UI/Toast";
import dynamic from "next/dynamic";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useMap } from "@/hooks/useMap";
import { LeftSidebar } from "@/components/Layout/LeftSidebar";
import { RightPanel } from "@/components/Layout/RightPanel";
import { BottomStatusBar } from "@/components/Layout/BottomStatusBar";
import { CyberTerminal } from "@/components/Map/CyberTerminal";
import { BlinkMode } from "@/components/Map/BlinkMode";
import { MapLegend } from "@/components/Map/MapLegend";
import { HYDERABAD_HOTSPOT_TEMPLATES } from "@/data/hyderabad-zones";
import type { AnalysisRequest, AnalysisResult } from "@/types";
import type { MapContainerRef } from "@/components/Map/MapContainer";

// Leaflet must be dynamically imported (no SSR)
const MapContainer = dynamic(
  () => import("@/components/Map/MapContainer").then((m) => m.MapContainer),
  { ssr: false }
);

export default function HomePage() {
  const analysis = useAnalysis();
  const map = useMap();
  const mapContainerRef = useRef<MapContainerRef>(null);
  const [mapZoom, setMapZoom] = useState<number>(11);
  const { toasts, toast, removeToast } = useToast();
  const [showTerminal, setShowTerminal] = useState(true);

  // --- Analysis Submission ---
  const handleSubmit = async (
    date1: string,
    date2: string,
    maxCloudCover: number
  ) => {
    if (!map.drawnAOI) return;

    const request: AnalysisRequest = {
      aoi: map.drawnAOI,
      date1,
      date2,
      max_cloud_cover: maxCloudCover,
    };

    setShowTerminal(true);
    await analysis.submit(request);
  };

  // --- Toast on pipeline completion ---
  const prevStatusRef = useRef<string | null>(null);
  if (analysis.status !== prevStatusRef.current) {
    if (analysis.status === "completed" && prevStatusRef.current === "running") {
      setTimeout(() => toast("✓ Pipeline execution successful! Results are ready.", "success"), 100);
    } else if (analysis.status === "failed" && prevStatusRef.current === "running") {
      setTimeout(() => toast(`✕ Pipeline failed: ${analysis.error || "Unknown error"}`, "error"), 100);
    }
    prevStatusRef.current = analysis.status;
  }


  // --- Load History ---
  const handleLoadHistory = useCallback((job: AnalysisResult) => {
    console.log("handleLoadHistory triggered with job:", job.job_id);
    console.log("Job metadata:", job.metadata);

    // Reconstruct AOI from metadata
    if (job.metadata?.bbox) {
      console.log("BBox found:", job.metadata.bbox);
      const [west, south, east, north] = job.metadata.bbox;
      const aoi = {
        type: "Polygon",
        coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
      };
      map.setDrawnAOI(aoi);
      
      const centerLat = (south + north) / 2;
      const centerLng = (west + east) / 2;
      console.log(`Flying map to [${centerLng}, ${centerLat}]`);
      
      // Use the ref directly for 100% reliability
      setTimeout(() => {
        if (mapContainerRef.current) {
          mapContainerRef.current.flyTo([centerLng, centerLat], 12);
        } else {
          window.dispatchEvent(new CustomEvent('map:flyTo', { detail: { center: [centerLng, centerLat], zoom: 12 } }));
        }
      }, 100);
    } else {
      console.warn("No bbox found in job metadata!");
    }
    analysis.setResult(job);
    toast("Historical job loaded successfully.", "info");
  }, [map, analysis, toast]);

  // --- PDF Export ---
  const handleDownloadPDF = useCallback(() => {
    if (analysis.result?.outputs?.pdf) {
      const apiBase = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/v1";
      const url = `${apiBase}/download/${analysis.result.job_id}/pdf`;
      const a = document.createElement("a");
      a.href = url;
      a.download = "geosentinel_report.pdf";
      a.click();
    }
  }, [analysis.result]);

  // Build hotspots from analysis data (or use templates)
  const hotspots = analysis.result
    ? HYDERABAD_HOTSPOT_TEMPLATES.map((h) => ({
        ...h,
        changeKm2: analysis.result?.area_change?.total_area_km2 ?? 0,
      }))
    : [];

  // Helper for generating API download URLs from dict keys
  const getDownloadUrl = (key: string) => {
    if (!analysis.result?.job_id || !key || !analysis.result.outputs?.[key]) return "";
    const apiBase = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/v1";
    return `${apiBase}/download/${analysis.result.job_id}/${key}`;
  };

  return (
    <div className="app-layout">
      {/* Map (Background) */}
      <main className="app-main" role="main" aria-label="Geospatial map">
        <MapContainer
          ref={mapContainerRef}
          onAOIDrawn={map.setDrawnAOI}
          onDrawingModeChange={map.setDrawingMode}
          onZoomChange={setMapZoom}
          drawnAOI={map.drawnAOI}
          layers={map.layers}
          result={analysis.result}
          blinkMode={map.blinkMode}
          blinkFrame={map.blinkFrame}
          lakeRadarActive={map.lakeRadarActive}
          showZones={map.showZones}
        />

        {/* CyberTerminal — immersive log viewer */}
        <CyberTerminal
          isVisible={analysis.isLoading && showTerminal}
          progressMessage={analysis.progressMessage}
          progressSteps={analysis.progressSteps}
          status={analysis.status || "queued"}
          onClose={() => setShowTerminal(false)}
          logs={analysis.logs}
        />

        {/* Blink Mode Controls */}
        {analysis.result && (
          <BlinkMode
            isActive={map.blinkMode}
            onToggle={map.toggleBlinkMode}
            currentFrame={map.blinkFrame}
            speed={map.blinkSpeed}
            onSpeedChange={map.setBlinkSpeed}
          />
        )}

        {/* Map Legend (Always available if analysis is loaded) */}
        {analysis.result && (
          <MapLegend layers={map.layers} blinkMode={map.blinkMode} />
        )}
      </main>

      {/* Floating UI Overlays */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {/* ------------------------------------------------------------------ */}
      {/* Header                                                               */}
      {/* ------------------------------------------------------------------ */}
      <header className="app-header">
        <div className="app-header-logo">
          <div className="app-header-logo-icon">
            {/* Satellite icon — neon cyan */}
            <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 28, height: 28 }}>
              <rect x="10" y="10" width="8" height="8" rx="1" fill="#38bdf8" />
              <rect x="4" y="12" width="6" height="4" rx="0.5" fill="#7dd3fc" />
              <rect x="18" y="12" width="6" height="4" rx="0.5" fill="#7dd3fc" />
              <circle cx="14" cy="14" r="2" fill="#0ea5e9" />
              <line x1="14" y1="2" x2="14" y2="7" stroke="#38bdf8" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="14" y1="21" x2="14" y2="26" stroke="#38bdf8" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <div className="app-header-title">GeoSentinel AI</div>
            <div className="app-header-subtitle">Hyderabad Metropolitan Region</div>
          </div>
        </div>

        <div className="app-header-spacer" />

        <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>

          <span className="app-header-badge">Sentinel-2 L2A</span>
          <span className="app-header-badge">CDSE</span>
          <span className="app-header-badge">EPSG:4326</span>
        </div>
      </header>

      {/* ------------------------------------------------------------------ */}
      {/* Workspace                                                            */}
      {/* ------------------------------------------------------------------ */}
      <div className="app-workspace">

        {/* Left Navigation + Content Panels */}
        <LeftSidebar
          onSubmit={handleSubmit}
          hasAOI={!!map.drawnAOI}
          isLoading={analysis.isLoading}
          onClearAOI={map.clearAOI}
          onDrawAOI={() => {
            const btn = document.getElementById("map-tool-draw-rect");
            if (btn) btn.click();
          }}
          isDrawingMode={map.isDrawingMode}
          result={analysis.result}
          layers={map.layers}
          toggleLayer={map.toggleLayer}
          onLoadHistory={handleLoadHistory}
          onDownloadPDF={handleDownloadPDF}
          blinkMode={map.blinkMode}
          onToggleBlinkMode={map.toggleBlinkMode}
          lakeRadarActive={map.lakeRadarActive}
          onToggleLakeRadar={map.toggleLakeRadar}
          showZones={map.showZones}
          onToggleZones={map.toggleZones}
        />

        {/* Right Results Panel */}
        {analysis.result && (
          <RightPanel
            result={analysis.result}
            isLoading={analysis.isLoading}
            progressMessage={analysis.progressMessage}
            jobId={analysis.jobId}
          />
        )}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Bottom Status Bar                                                    */}
      {/* ------------------------------------------------------------------ */}
      <BottomStatusBar
        status={analysis.status}
        message={analysis.progressMessage}
        error={analysis.error}
        zoom={mapZoom}
      />
    </div>
  );
}
