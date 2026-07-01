"use client";

// =============================================================================
// GeoSentinel AI — Main Page
// =============================================================================

import dynamic from "next/dynamic";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useMap } from "@/hooks/useMap";
import { AnalysisForm } from "@/components/Sidebar/AnalysisForm";
import { ResultsDashboard } from "@/components/Dashboard/ResultsDashboard";
import { StatusBar } from "@/components/UI/StatusBar";
import type { AnalysisRequest } from "@/types";

// Leaflet must be imported dynamically (no SSR)
const MapContainer = dynamic(
  () => import("@/components/Map/MapContainer").then((m) => m.MapContainer),
  { ssr: false }
);

export default function HomePage() {
  const analysis = useAnalysis();
  const map = useMap();

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
      {/* ------------------------------------------------------------------ */}
      {/* Header                                                              */}
      {/* ------------------------------------------------------------------ */}
      <header className="app-header">
        <div className="header-logo">
          <div className="header-logo-icon">🛰️</div>
          <div>
            <div className="header-title">GeoSentinel AI</div>
            <div className="header-subtitle">Hyderabad Metropolitan Region</div>
          </div>
        </div>

        <div className="header-spacer" />

        <div className="header-badge">Sentinel-2 L2A</div>
        <div className="header-badge">CDSE</div>
      </header>

      {/* ------------------------------------------------------------------ */}
      {/* Sidebar                                                             */}
      {/* ------------------------------------------------------------------ */}
      <aside className="app-sidebar">
        <div className="scroll-area">
          <AnalysisForm
            onSubmit={handleSubmit}
            hasAOI={!!map.drawnAOI}
            isLoading={analysis.isLoading}
            onClearAOI={map.clearAOI}
          />
        </div>
      </aside>

      {/* ------------------------------------------------------------------ */}
      {/* Map                                                                 */}
      {/* ------------------------------------------------------------------ */}
      <main className="app-main">
        <MapContainer
          onAOIDrawn={map.setDrawnAOI}
          onDrawingModeChange={map.setDrawingMode}
          drawnAOI={map.drawnAOI}
        />

        {/* Results Dashboard Overlay */}
        {analysis.result && (
          <div className="dashboard-overlay">
            <ResultsDashboard result={analysis.result} />
          </div>
        )}

        {/* Status Bar */}
        {(analysis.isLoading || analysis.status === "completed" || analysis.error) && (
          <StatusBar
            status={analysis.status}
            message={analysis.progressMessage}
            error={analysis.error}
            onClose={analysis.reset}
          />
        )}
      </main>
    </div>
  );
}
