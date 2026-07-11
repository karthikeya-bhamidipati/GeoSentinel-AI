"use client";

// =============================================================================
// GeoSentinel AI — Main Page
// Professional GIS application layout: Map-first, no landing page.
// =============================================================================

import { useState, useRef } from "react";
import { useToast } from "@/hooks/useToast";
import { ToastContainer } from "@/components/UI/Toast";
import dynamic from "next/dynamic";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useMap } from "@/hooks/useMap";
import { LeftSidebar } from "@/components/Layout/LeftSidebar";
import { RightPanel } from "@/components/Layout/RightPanel";
import { BottomStatusBar } from "@/components/Layout/BottomStatusBar";
import { PipelineProgressOverlay } from "@/components/Map/PipelineProgressOverlay";
import type { AnalysisRequest } from "@/types";
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
  const { toasts, removeToast } = useToast();

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

    await analysis.submit(request);
  };

  return (
    <div className="app-layout">
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      {/* ------------------------------------------------------------------ */}
      {/* Header                                                               */}
      {/* ------------------------------------------------------------------ */}
      <header className="app-header">
        <div className="app-header-logo">
          <div className="app-header-logo-icon">
            {/* Satellite icon */}
            <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 28, height: 28 }}>
              <rect x="10" y="10" width="8" height="8" rx="1" fill="#60a5fa" />
              <rect x="4" y="12" width="6" height="4" rx="0.5" fill="#93c5fd" />
              <rect x="18" y="12" width="6" height="4" rx="0.5" fill="#93c5fd" />
              <circle cx="14" cy="14" r="2" fill="#1d6fa4" />
              <line x1="14" y1="2" x2="14" y2="7" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="14" y1="21" x2="14" y2="26" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <div className="app-header-title">GeoSentinel AI</div>
            <div className="app-header-subtitle">Hyderabad Metropolitan Region</div>
          </div>
        </div>

        <div className="app-header-spacer" />

        <div style={{ display: "flex", gap: "var(--space-2)" }}>
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
          onLoadHistory={(job) => {
            map.setDrawnAOI(job.aoi);
            analysis.setResult(job);
          }}
        />

        {/* Map */}
        <main className="app-main" role="main" aria-label="Geospatial map">
          <MapContainer
            ref={mapContainerRef}
            onAOIDrawn={map.setDrawnAOI}
            onDrawingModeChange={map.setDrawingMode}
            onZoomChange={setMapZoom}
            drawnAOI={map.drawnAOI}
            layers={map.layers}
            result={analysis.result}
          />

          {/* Pipeline progress overlay — appears on top of map during analysis */}
          <PipelineProgressOverlay
            isVisible={analysis.isLoading}
            message={analysis.progressMessage}
            completedSteps={analysis.progressSteps}
          />
        </main>

        {/* Right Results Panel */}
        <RightPanel
          result={analysis.result}
          isLoading={analysis.isLoading}
          progressMessage={analysis.progressMessage}
          jobId={analysis.jobId}
        />
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
