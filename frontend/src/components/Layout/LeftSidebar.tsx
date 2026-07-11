"use client";

// =============================================================================
// GeoSentinel AI — Left Navigation Sidebar
// Professional GIS icon strip (ArcGIS Pro style)
// =============================================================================

import React, { useState } from "react";
import { AnalysisForm } from "@/components/Sidebar/AnalysisForm";
import { LayerManager } from "@/components/Map/LayerManager";
import { HistoryList } from "@/components/Sidebar/HistoryList";
import type { Layer } from "@/hooks/useMap";

// ---------------------------------------------------------------------------
// Icon set (inline SVG for zero-dependency icons)
// ---------------------------------------------------------------------------

const Icons = {
  Analysis: () => (
    <svg viewBox="0 0 20 20" fill="currentColor">
      <path d="M3 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 7a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3zm7-7a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1V4zm0 7a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-3z"/>
    </svg>
  ),
  Layers: () => (
    <svg viewBox="0 0 20 20" fill="currentColor">
      <path d="M10 2L2 7l8 5 8-5-8-5zM2 13l8 5 8-5M2 10l8 5 8-5"/>
    </svg>
  ),
  Chart: () => (
    <svg viewBox="0 0 20 20" fill="currentColor">
      <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zm6-4a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zm6-3a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
    </svg>
  ),
  Reports: () => (
    <svg viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd"/>
    </svg>
  ),
  Benchmark: () => (
    <svg viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
    </svg>
  ),
  Settings: () => (
    <svg viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd"/>
    </svg>
  ),
  Help: () => (
    <svg viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"/>
    </svg>
  ),
  History: () => (
    <svg viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
    </svg>
  ),
};

// ---------------------------------------------------------------------------
// Section panels rendered when a nav item is active
// ---------------------------------------------------------------------------

type NavSection = "analysis" | "layers" | "history" | "reports" | "benchmark" | "settings" | "help" | null;

interface LeftSidebarProps {
  onSubmit: (date1: string, date2: string, maxCloudCover: number) => Promise<void>;
  hasAOI: boolean;
  isLoading: boolean;
  onClearAOI: () => void;
  onDrawAOI: () => void;
  isDrawingMode: boolean;
  result?: any;
  layers: Layer[];
  toggleLayer: (id: string) => void;
  onLoadHistory?: (job: any) => void;
}

export function LeftSidebar({ onSubmit, hasAOI, isLoading, onClearAOI, onDrawAOI, isDrawingMode, result, layers, toggleLayer, onLoadHistory }: LeftSidebarProps) {
  const [activeSection, setActiveSection] = useState<NavSection>("analysis");

  const toggleSection = (section: NavSection) => {
    setActiveSection(prev => prev === section ? null : section);
  };

  const navItems = [
    { id: "analysis" as NavSection, label: "Analysis", Icon: Icons.Analysis },
    { id: "layers" as NavSection, label: "Layers", Icon: Icons.Layers },
    { id: "history" as NavSection, label: "History", Icon: Icons.History },
    { id: "reports" as NavSection, label: "Reports", Icon: Icons.Reports },
    { id: "benchmark" as NavSection, label: "Bench", Icon: Icons.Benchmark },
  ];

  const bottomNavItems = [
    { id: "settings" as NavSection, label: "Settings", Icon: Icons.Settings },
    { id: "help" as NavSection, label: "Help", Icon: Icons.Help },
  ];

  return (
    <>
      {/* Icon Strip */}
      <nav className="nav-sidebar" aria-label="Main navigation">
        {navItems.map(({ id, label, Icon }) => (
          <button
            key={id}
            id={`nav-${id}`}
            className={`nav-sidebar-item${activeSection === id ? " active" : ""}`}
            onClick={() => toggleSection(id)}
            title={label}
            aria-pressed={activeSection === id}
          >
            <Icon />
            <span className="nav-sidebar-label">{label}</span>
          </button>
        ))}

        <div className="nav-sidebar-spacer" />
        <div className="nav-sidebar-divider" />

        {bottomNavItems.map(({ id, label, Icon }) => (
          <button
            key={id}
            id={`nav-${id}`}
            className={`nav-sidebar-item${activeSection === id ? " active" : ""}`}
            onClick={() => toggleSection(id)}
            title={label}
            aria-pressed={activeSection === id}
          >
            <Icon />
            <span className="nav-sidebar-label">{label}</span>
          </button>
        ))}
      </nav>

      {/* Content Panel */}
      {activeSection && (
        <div className="content-panel" role="complementary">
          <SectionHeader title={getSectionTitle(activeSection)} onClose={() => setActiveSection(null)} />
          <div className="content-panel-body">
            {activeSection === "analysis" && (
              <AnalysisForm
                onSubmit={onSubmit}
                hasAOI={hasAOI}
                isLoading={isLoading}
                onClearAOI={onClearAOI}
                onDrawAOI={onDrawAOI}
                isDrawingMode={isDrawingMode}
              />
            )}
            {activeSection === "layers" && <LayerManager layers={layers} onToggleLayer={toggleLayer} />}
            {activeSection === "history" && <HistoryList onLoadHistory={onLoadHistory} />}

            {activeSection === "reports" && <ReportsHint result={result} />}
            {activeSection === "benchmark" && <BenchmarkLink />}
            {activeSection === "settings" && <SettingsLink />}
            {activeSection === "help" && <HelpContent />}
          </div>
        </div>
      )}
    </>
  );
}

function getSectionTitle(section: NavSection): string {
  const map: Record<string, string> = {
    analysis: "Analysis Setup",
    layers: "Layer Manager",
    history: "Analysis History",
    analytics: "Analytics",
    reports: "Reports",
    benchmark: "Model Benchmark",
    settings: "Settings",
    help: "Help",
  };
  return section ? map[section] ?? section : "";
}

function SectionHeader({ title, onClose }: { title: string; onClose: () => void }) {
  return (
    <div className="content-panel-header">
      <span className="content-panel-title">{title}</span>
      <button
        onClick={onClose}
        className="btn btn-ghost btn-sm"
        style={{ width: 24, height: 24, padding: 0, marginRight: -4 }}
        aria-label="Close panel"
      >
        ×
      </button>
    </div>
  );
}

function AnalyticsHint() {
  return (
    <div className="empty-state" style={{ paddingTop: "var(--space-8)" }}>
      <svg className="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
      <p className="empty-state-title">Charts Available After Analysis</p>
      <p className="empty-state-text">Run an analysis to view temporal charts and spatial statistics.</p>
    </div>
  );
}

function ReportsHint({ result }: { result: any }) {
  if (!result) {
    return (
      <div className="empty-state" style={{ paddingTop: "var(--space-8)" }}>
        <svg className="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
        <p className="empty-state-title">No Reports Yet</p>
        <p className="empty-state-text">Complete an analysis to download PDF, CSV, and GeoJSON reports.</p>
      </div>
    );
  }

  const downloads = [
    { key: "image_t1_png", label: "T1 True-Color Image (PNG)", ext: ".png", icon: "🛰️" },
    { key: "image_t2_png", label: "T2 True-Color Image (PNG)", ext: ".png", icon: "🛰️" },
    { key: "mask_t1", label: "T1 Land Cover Mask (PNG)", ext: ".png", icon: "🗺️" },
    { key: "mask_t2", label: "T2 Land Cover Mask (PNG)", ext: ".png", icon: "🗺️" },
    { key: "change_map_png", label: "Change Map (PNG)", ext: ".png", icon: "📍" },
    { key: "pdf", label: "PDF Report", ext: ".pdf", icon: "📄" },
    { key: "csv", label: "Area Statistics CSV", ext: ".csv", icon: "📊" },
    { key: "recommendations_csv", label: "Recommendations CSV", ext: ".csv", icon: "📋" },
    { key: "mask_png", label: "Land Cover Map (PNG)", ext: ".png", icon: "🗺️" },
    { key: "ndvi_delta_png", label: "NDVI Change Map (PNG)", ext: ".png", icon: "🌿" },
  ];

  return (
    <div>
      <p className="text-muted text-xs" style={{ marginBottom: "var(--space-3)" }}>
        Analysis complete. Download report files below.
      </p>
      {downloads.map(({ key, label, icon }) => {
        const url = result.outputs?.[key];
        if (!url) return null;
        const apiBase = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/v1";
        return (
          <a
            key={key}
            href={`${apiBase}/download/${result.job_id}/${key}`}
            className="download-btn"
            download
          >
            <span>{icon}</span>
            <span style={{ flex: 1 }}>{label}</span>
            <svg style={{ width: 14, height: 14 }} viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </a>
        );
      })}
    </div>
  );
}

function BenchmarkLink() {
  return (
    <div>
      <p className="text-sm text-muted" style={{ marginBottom: "var(--space-3)", lineHeight: 1.6 }}>
        Compare U-Net and DeepLabV3+ segmentation performance across benchmark datasets (OSCD, S2Looking).
      </p>
      <a href="/benchmark" className="btn btn-primary btn-full">
        Open Benchmark Dashboard →
      </a>
    </div>
  );
}

function SettingsLink() {
  return (
    <div>
      <p className="text-sm text-muted" style={{ marginBottom: "var(--space-3)", lineHeight: 1.6 }}>
        Configure CDSE credentials, cache paths, model checkpoints, and platform preferences.
      </p>
      <a href="/settings" className="btn btn-secondary btn-full">
        Open Settings →
      </a>
    </div>
  );
}

function HelpContent() {
  const steps = [
    "Draw an AOI on the map using the Analysis tab",
    "Select T1 (before) and T2 (after) dates",
    "Set maximum cloud cover tolerance",
    "Click Run Analysis",
    "Monitor pipeline progress",
    "View results in the right panel",
    "Download PDF/CSV reports",
  ];

  return (
    <div>
      <div className="form-section-title" style={{ marginBottom: "var(--space-3)" }}>Workflow</div>
      {steps.map((step, i) => (
        <div key={i} style={{ display: "flex", gap: "var(--space-2)", marginBottom: "var(--space-2)", alignItems: "flex-start" }}>
          <span style={{
            width: 18, height: 18, borderRadius: "50%", background: "var(--color-primary)",
            color: "white", fontSize: 10, fontWeight: 700, display: "flex",
            alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 1
          }}>{i + 1}</span>
          <span className="text-sm" style={{ color: "var(--color-text-secondary)" }}>{step}</span>
        </div>
      ))}
      <div style={{ marginTop: "var(--space-4)", padding: "var(--space-3)", background: "var(--color-info-bg)", border: "1px solid var(--color-info-border)", borderRadius: "var(--radius-sm)" }}>
        <p className="text-xs" style={{ color: "var(--color-info)" }}>
          <strong>Data Source:</strong> Copernicus Data Space Ecosystem (CDSE), Sentinel-2 Level-2A. 
          Set CDSE_USERNAME and CDSE_PASSWORD in your .env file.
        </p>
      </div>
    </div>
  );
}
