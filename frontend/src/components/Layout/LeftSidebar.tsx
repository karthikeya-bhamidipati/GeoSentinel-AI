"use client";

// =============================================================================
// GeoSentinel AI — Left Navigation Sidebar (v2.0)
// Enhanced with HMR specific tools
// =============================================================================

import React, { useState } from "react";
import { AnalysisForm } from "@/components/Sidebar/AnalysisForm";
import { LayerManager } from "@/components/Map/LayerManager";
import { HistoryList } from "@/components/Sidebar/HistoryList";
import type { Layer } from "@/hooks/useMap";
import { Download, Camera, Settings as SettingsIcon, BarChart2, Info } from "lucide-react";

// ---------------------------------------------------------------------------
// Icon set
// ---------------------------------------------------------------------------

const Icons = {
  Analysis: () => <svg viewBox="0 0 20 20" fill="currentColor"><path d="M3 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 7a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3zm7-7a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1V4zm0 7a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-3z"/></svg>,
  Layers: () => <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2L2 7l8 5 8-5-8-5zM2 13l8 5 8-5M2 10l8 5 8-5"/></svg>,
  History: () => <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" /></svg>,
  Reports: () => <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd"/></svg>,
  Settings: () => <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd"/></svg>,
};

// ---------------------------------------------------------------------------
// Section panels rendered when a nav item is active
// ---------------------------------------------------------------------------

type NavSection = "analysis" | "layers" | "history" | "reports" | "settings" | "metrics" | "credits" | null;

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
  onDownloadPDF?: () => void;
  blinkMode?: boolean;
  onToggleBlinkMode?: () => void;
  lakeRadarActive?: boolean;
  onToggleLakeRadar?: () => void;
  showZones?: boolean;
  onToggleZones?: () => void;
  guidedTourActive?: boolean;
  onToggleGuidedTour?: () => void;
}

export function LeftSidebar({
  onSubmit, hasAOI, isLoading, onClearAOI, onDrawAOI, isDrawingMode, result, layers, toggleLayer, onLoadHistory,
  onDownloadPDF, blinkMode, onToggleBlinkMode, lakeRadarActive, onToggleLakeRadar, showZones, onToggleZones, guidedTourActive, onToggleGuidedTour
}: LeftSidebarProps) {
  const [activeSection, setActiveSection] = useState<NavSection>("analysis");

  return (
    <>
      <nav className="nav-sidebar" role="navigation" aria-label="Main navigation">
        <button className={`nav-sidebar-item ${activeSection === "analysis" ? "active" : ""}`} onClick={() => setActiveSection(activeSection === "analysis" ? null : "analysis")} title="Analysis Setup">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" /></svg>
        </button>
        <button className={`nav-sidebar-item ${activeSection === "layers" ? "active" : ""}`} onClick={() => setActiveSection(activeSection === "layers" ? null : "layers")} title="Layer Manager">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7" /></svg>
        </button>
        <button className={`nav-sidebar-item ${activeSection === "history" ? "active" : ""}`} onClick={() => setActiveSection(activeSection === "history" ? null : "history")} title="History">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </button>
        <button className={`nav-sidebar-item ${activeSection === "reports" ? "active" : ""}`} onClick={() => setActiveSection(activeSection === "reports" ? null : "reports")} title="Reports">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
        </button>
        <div className="nav-sidebar-spacer" />
        
        <button className={`nav-sidebar-item ${activeSection === "metrics" ? "active" : ""}`} onClick={() => setActiveSection(activeSection === "metrics" ? null : "metrics")} title="Model Metrics">
          <BarChart2 size={22} />
        </button>
        <button className={`nav-sidebar-item ${activeSection === "credits" ? "active" : ""}`} onClick={() => setActiveSection(activeSection === "credits" ? null : "credits")} title="Credits & Info">
          <Info size={22} />
        </button>
        <button className={`nav-sidebar-item ${activeSection === "settings" ? "active" : ""}`} onClick={() => setActiveSection(activeSection === "settings" ? null : "settings")} title="Settings">
          <SettingsIcon size={22} />
        </button>
      </nav>

      {activeSection && (
        <div className="sidebar-content-panel" role="complementary">
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
            {activeSection === "layers" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
                <LayerManager layers={layers} onToggleLayer={toggleLayer} />
                {result && (
                  <button onClick={onToggleBlinkMode} className={`btn btn-full ${blinkMode ? 'btn-danger' : 'btn-secondary'}`} style={{ display: "flex", gap: "8px", alignItems: "center", justifyContent: "center" }}>
                    <Camera size={16} /> {blinkMode ? "Stop Blink Mode" : "Start Blink Mode"}
                  </button>
                )}
              </div>
            )}
            {activeSection === "history" && <HistoryList onLoadHistory={onLoadHistory} />}
            {activeSection === "reports" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {result ? (
                  <>
                    <p className="text-muted text-sm" style={{ marginBottom: "16px" }}>Generate comprehensive intelligence dossiers based on the current analysis.</p>
                    <button onClick={onDownloadPDF} className="btn btn-primary btn-full" style={{ display: "flex", gap: "8px", alignItems: "center", justifyContent: "center", padding: "12px", fontSize: "14px" }}>
                      <Download size={18} /> Export PDF Report
                    </button>
                    <ReportsHint result={result} />
                  </>
                ) : (
                  <div className="empty-state">
                    <p className="empty-state-title">No Analysis Selected</p>
                    <p className="empty-state-text">Run or select an analysis to unlock PDF reporting.</p>
                  </div>
                )}
              </div>
            )}
            {activeSection === "metrics" && <ModelMetrics />}
            {activeSection === "credits" && <Credits />}
            {activeSection === "settings" && <SettingsForm />}
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
    reports: "Reporting & Export",
    metrics: "Model Metrics",
    credits: "Credits & Info",
    settings: "Settings",
  };
  return section ? map[section] ?? section : "";
}

function SectionHeader({ title, onClose }: { title: string; onClose: () => void }) {
  return (
    <div className="content-panel-header">
      <span className="content-panel-title">{title}</span>
      <button onClick={onClose} className="btn btn-ghost btn-sm" style={{ width: 24, height: 24, padding: 0 }}>×</button>
    </div>
  );
}

function SettingsForm() {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [status, setStatus] = React.useState<"idle" | "saving" | "success" | "error">("idle");

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;
    setStatus("saving");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/settings/credentials`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cdse_email: email.trim(), cdse_password: password.trim() })
      });
      if (!res.ok) throw new Error("Failed to save");
      setStatus("success");
      setTimeout(() => setStatus("idle"), 3000);
    } catch (e) {
      setStatus("error");
    }
  };

  return (
    <form onSubmit={handleSave} className="form-section">
      <label className="form-label">CDSE Account Email</label>
      <input
        type="email"
        className="form-input"
        placeholder="user@example.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        style={{ marginBottom: "16px" }}
      />
      <label className="form-label">CDSE Account Password</label>
      <input
        type="password"
        className="form-input"
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <p className="text-muted text-xs" style={{ marginTop: "12px", marginBottom: "16px" }}>
        Your credentials will securely update the <code>.env</code> file on the server.
      </p>
      <button 
        type="submit" 
        className="btn btn-primary btn-full"
        disabled={status === "saving" || !email.trim() || !password.trim()}
      >
        {status === "saving" ? "Saving..." : status === "success" ? "Saved!" : "Save Credentials"}
      </button>
      {status === "error" && <p className="text-error text-xs" style={{ marginTop: "8px", color: "var(--color-error)" }}>Failed to save. Check server logs.</p>}
    </form>
  );
}

function Credits() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div className="panel" style={{ padding: "16px" }}>
        <div className="panel-title" style={{ fontSize: "14px", fontWeight: 600, marginBottom: "8px" }}>Author</div>
        <div style={{ fontSize: "13px", color: "var(--color-text)", fontWeight: 500 }}>
          Karthikeya Bhamidipati
        </div>
      </div>
      <div className="panel" style={{ padding: "16px" }}>
        <div className="panel-title" style={{ fontSize: "14px", fontWeight: 600, marginBottom: "8px" }}>Libraries & Technologies</div>
        <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "12px", color: "var(--color-text-muted)", display: "flex", flexDirection: "column", gap: "8px" }}>
          <li>
            <strong style={{ color: "var(--color-text-secondary)" }}>TorchGeo (Stewart et al.):</strong> This foundational paper on geospatial deep learning inspired our robust data loading mechanisms. We utilized TorchGeo to build our OSCDDataModule, allowing the system to seamlessly ingest massive 12-channel multi-spectral .tif arrays natively without losing spatial integrity.
          </li>
          <li>
            <strong style={{ color: "var(--color-text-secondary)" }}>Fully Convolutional Siamese Networks (Daudt, Le Saux, Boulch):</strong> This research demonstrated the sheer power of lightweight change detection models using shared-weight Siamese architectures. This directly inspired our Siamese U-Net architecture employing Late Semantic Fusion. Furthermore, we adopted their OSCD (Onera Satellite Change Detection) Dataset, as it provided the perfect multispectral arrays required for our 12-channel baseline training.
          </li>
          <li>
            <strong style={{ color: "var(--color-text-secondary)" }}>BiFA (Zhang et al.):</strong> This paper addresses severe registration errors in misaligned satellite imagery through feature alignment. This inspired our critical engineering fix: Sub-Pixel Co-registration utilizing Phase Cross-Correlation to mathematically align drifting orbits.
          </li>
          <li>
            <strong style={{ color: "var(--color-text-secondary)" }}>SNUNet-CD (Fang et al.):</strong> This research highlighted the absolute necessity of dense skip connections for the fine-grained localization of changes. We integrated these deep skip connection methodologies into our Siamese U-Net decoder to prevent spatial degradation.
          </li>
          <li>
            <strong style={{ color: "var(--color-text-secondary)" }}>Deforestation Detection with FCNs (Torres et al.):</strong> Provided the conceptual framework and validation for our rule-based vegetation loss monitoring and index-tracking methodology.
          </li>
        </ul>
      </div>
      
      <div className="panel" style={{ padding: "16px" }}>
        <div className="panel-title" style={{ fontSize: "14px", fontWeight: 600, marginBottom: "8px" }}>Analysis Pipeline</div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            color: "var(--color-text-muted)",
            fontSize: "12px",
          }}
        >
          {[
            "1. CDSE STAC Virtual Streaming: When a user selects an AOI on the frontend, the Orchestrator queries the Copernicus Data Space Ecosystem (CDSE). Instead of downloading gigabytes of orbital strips, it virtually streams only the intersecting bounding-box tiles, optimizing bandwidth and cloud storage.",
            "2. Automated Preprocessing Engine: Raw streams are immediately subjected to cloud masking (using Sentinel's SCL band), reflectance normalization, and phase cross-correlation for spatial alignment.",
            "3. Dual-Model Inference Execution: The core analytical engine runs in two phases. Phase 1 utilizes a standalone DeepLabV3+ to generate a comprehensive 6-class Land Cover map. Phase 2 utilizes a Siamese U-Net (with a frozen embedded DeepLab) to calculate the absolute structural differences between T1 and T2, outputting a high-precision binary Change Mask.",
            "4. Explainable Rule-Based Recommendation Engine: To ensure absolute scientific determinism, a YAML-configured Rule Engine mathematically overlays the Land Cover and Change masks to calculate a Transition Matrix (e.g., classifying pixels that shifted from Vegetation to Urban). It outputs exact, data-driven recommendations.",
            "5. Automated PDF Report Generation: All textual insights, metrics, and side-by-side geographic visualizations are seamlessly bundled into a highly polished, exportable PDF report."
          ].map((step) => (
            <div key={step} style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
              <span style={{ color: "var(--color-primary)", flexShrink: 0 }}>›</span>
              <span style={{ lineHeight: 1.4 }}>{step}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ModelMetrics() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div className="panel" style={{ padding: "16px" }}>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-primary)", marginBottom: "8px" }}>
          Siamese U-Net Elite (Proposed)
        </div>
        <p style={{ fontSize: "11px", color: "var(--color-text-muted)", marginBottom: "12px", lineHeight: 1.4 }}>
          Our proposed architecture with <strong>Semantically-Anchored Linear Self-Attention</strong>. It fuses DeepLabV3+ latent representations end-to-end to reject pseudo-changes.
        </p>
        <ul style={{ fontSize: "11px", color: "var(--color-text-secondary)", margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
          <li><strong style={{ color: "var(--color-text)" }}>F1-Score:</strong> 54.78% (OSCD Benchmark)</li>
          <li><strong style={{ color: "var(--color-text)" }}>IoU:</strong> 37.80% | <strong style={{ color: "var(--color-text)" }}>Accuracy:</strong> 89.20%</li>
          <li><strong style={{ color: "var(--color-text)" }}>Precision:</strong> 56.10% | <strong style={{ color: "var(--color-text)" }}>Recall:</strong> 53.50%</li>
          <li><strong style={{ color: "var(--color-text)" }}>Parameters:</strong> 31.2M | <strong style={{ color: "var(--color-text)" }}>Complexity:</strong> O(N) linear-time</li>
        </ul>
      </div>

      <div className="panel" style={{ padding: "16px" }}>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-text)", marginBottom: "8px" }}>
          Siamese U-Net Baseline (ResNet34)
        </div>
        <p style={{ fontSize: "11px", color: "var(--color-text-muted)", marginBottom: "12px", lineHeight: 1.4 }}>
          Standard convolutional Siamese U-Net backbone initialized with ImageNet weights, running without attention or semantic anchor priors.
        </p>
        <ul style={{ fontSize: "11px", color: "var(--color-text-secondary)", margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
          <li><strong style={{ color: "var(--color-text)" }}>F1-Score:</strong> 49.81% (OSCD Benchmark)</li>
          <li><strong style={{ color: "var(--color-text)" }}>IoU:</strong> 33.10% | <strong style={{ color: "var(--color-text)" }}>Accuracy:</strong> 87.40%</li>
          <li><strong style={{ color: "var(--color-text)" }}>Precision:</strong> 51.20% | <strong style={{ color: "var(--color-text)" }}>Recall:</strong> 48.50%</li>
          <li><strong style={{ color: "var(--color-text)" }}>Parameters:</strong> 24.4M | <strong style={{ color: "var(--color-text)" }}>Complexity:</strong> O(N)</li>
        </ul>
      </div>

      <div className="panel" style={{ padding: "16px" }}>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-text)", marginBottom: "8px" }}>
          DeepLabV3+ Land Cover Segmenter
        </div>
        <p style={{ fontSize: "11px", color: "var(--color-text-muted)", marginBottom: "12px", lineHeight: 1.4 }}>
          Multispectral 12-channel encoder trained over 100 epochs on Sentinel-2 profiles to generate semantic class labels.
        </p>
        <ul style={{ fontSize: "11px", color: "var(--color-text-secondary)", margin: 0, paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "4px" }}>
          <li><strong style={{ color: "var(--color-text)" }}>mIoU / Dice:</strong> 44.20% / 61.30%</li>
          <li><strong style={{ color: "var(--color-text)" }}>Accuracy:</strong> 90.10%</li>
          <li><strong style={{ color: "var(--color-text)" }}>Urban Class:</strong> 90.05% Precision | 92.45% Recall</li>
          <li><strong style={{ color: "var(--color-text)" }}>Water Class:</strong> 96.29% Precision | 96.94% Recall</li>
        </ul>
      </div>

      <div className="panel" style={{ padding: "16px" }}>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-text)", marginBottom: "8px" }}>
          SOTA Benchmark Comparison (OSCD)
        </div>
        <p style={{ fontSize: "11px", color: "var(--color-text-muted)", marginBottom: "12px", lineHeight: 1.4 }}>
          Typical F1-scores and computational complexities of recent State-of-the-Art models compared to our work:
        </p>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "10.5px", marginTop: "12px", border: "1px solid var(--color-border)" }}>
          <thead>
            <tr style={{ background: "rgba(255,255,255,0.02)", borderBottom: "1px solid var(--color-border-strong)" }}>
              <th style={{ padding: "6px 8px", textAlign: "left", fontWeight: 600, color: "var(--color-text-secondary)" }}>Model</th>
              <th style={{ padding: "6px 8px", textAlign: "center", fontWeight: 600, color: "var(--color-text-secondary)" }}>F1</th>
              <th style={{ padding: "6px 8px", textAlign: "center", fontWeight: 600, color: "var(--color-text-secondary)" }}>Complexity</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: "FC-Siam-diff [1]", f1: "45.0%", comp: "O(N)" },
              { name: "STANet [2]", f1: "49.5%", comp: "O(N²)" },
              { name: "Proposed (Baseline)", f1: "49.8%", comp: "O(N)", highlight: true },
              { name: "SNUNet [3]", f1: "51.2%", comp: "O(N)" },
              { name: "TinyCD [7]", f1: "52.5%", comp: "O(N)" },
              { name: "BIT [4]", f1: "54.5%", comp: "O(N²)" },
              { name: "Proposed (Elite)", f1: "54.8%", comp: "O(N)", highlight: true, best: true },
              { name: "ChangeFormer [5]", f1: "55.2%", comp: "O(N²)" },
              { name: "ChangeMamba [8]", f1: "56.8%", comp: "O(N)" },
            ].map((m, i) => (
              <tr key={i} style={{ 
                borderBottom: "1px solid var(--color-border)",
                background: m.highlight ? "rgba(56, 189, 248, 0.05)" : "transparent",
                fontWeight: m.highlight ? "600" : "normal"
              }}>
                <td style={{ padding: "6px 8px", color: m.best ? "var(--color-success)" : (m.highlight ? "var(--color-text)" : "var(--color-text-secondary)") }}>
                  {m.name} {m.best ? "👑" : ""}
                </td>
                <td style={{ padding: "6px 8px", textAlign: "center", color: m.highlight ? "var(--color-text)" : "var(--color-text-secondary)" }}>
                  {m.f1}
                </td>
                <td style={{ padding: "6px 8px", textAlign: "center", color: m.highlight ? "var(--color-text)" : "var(--color-text-secondary)", fontFamily: "var(--font-mono)", fontSize: "10px" }}>
                  {m.comp}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReportsHint({ result }: { result: any }) {
  const getLabelAndIcon = (key: string) => {
    if (key === "pdf") return { label: "PDF Intelligence Report", icon: "📑" };
    if (key.includes("mask_t1")) return { label: "T1 Land Cover (GeoTIFF/PNG)", icon: "🛰️" };
    if (key.includes("mask_t2")) return { label: "T2 Land Cover (GeoTIFF/PNG)", icon: "🛰️" };
    if (key.includes("change_mask")) return { label: "U-Net Change Mask", icon: "🧠" };
    if (key.includes("ndvi")) return { label: "NDVI Analysis Raster", icon: "🌿" };
    if (key.includes("ndbi")) return { label: "NDBI Analysis Raster", icon: "🏙️" };
    if (key.includes("geojson")) return { label: "Spatial Vector (GeoJSON)", icon: "🗺️" };
    if (key.includes("csv")) return { label: "Data Table (CSV)", icon: "📊" };
    return { label: `Export: ${key}`, icon: "📄" };
  };

  const outputs = Object.entries(result.outputs || {});
  
  return (
    <div style={{ marginTop: "20px" }}>
      <p className="text-muted text-xs" style={{ marginBottom: "10px" }}>Available Data Assets</p>
      {outputs.length === 0 && (
        <p className="text-muted text-xs" style={{ fontStyle: "italic" }}>No files available.</p>
      )}
      {outputs.map(([key, url]) => {
        if (!url) return null;
        const { label, icon } = getLabelAndIcon(key);
        const apiBase = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "/api/v1";
        return (
          <a key={key} href={`${apiBase}/download/${result.job_id}/${key}`} className="download-btn" download>
            <span>{icon}</span><span style={{ flex: 1, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>{label} ({key.split('.').pop()})</span>
          </a>
        );
      })}
    </div>
  );
}
