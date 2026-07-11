"use client";

// =============================================================================
// GeoSentinel AI — Settings Page
// CDSE credentials, model configuration, cache, theme preferences
// =============================================================================

import { useState } from "react";
import type { Metadata } from "next";

export default function SettingsPage() {
  const [cdseUsername, setCdseUsername] = useState("");
  const [cdsePassword, setCdsePassword] = useState("");
  const [modelPath, setModelPath] = useState("");
  const [cloudThreshold, setCloudThreshold] = useState(10);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real implementation, this would call a backend /settings endpoint
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)", fontFamily: "var(--font-sans)", color: "var(--color-text)" }}>
      {/* Header */}
      <header style={{ background: "var(--color-header)", color: "white", padding: "0 32px", height: 48, display: "flex", alignItems: "center", gap: 12 }}>
        <a href="/" style={{ color: "rgba(255,255,255,0.6)", textDecoration: "none", fontSize: 12 }}>← GeoSentinel AI</a>
        <span style={{ color: "rgba(255,255,255,0.3)", fontSize: 12 }}>/</span>
        <span style={{ fontSize: 14, fontWeight: 600, color: "white" }}>Settings</span>
      </header>

      <main style={{ maxWidth: 720, margin: "0 auto", padding: "32px 24px" }}>
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Platform Settings</h1>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: 4 }}>
            Configure CDSE data access, model inference, and analysis defaults.
          </p>
        </div>

        <form onSubmit={handleSave}>
          {/* CDSE Credentials */}
          <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, overflow: "hidden", marginBottom: 20 }}>
            <div style={{ padding: "10px 16px", background: "var(--color-surface-alt)", borderBottom: "1px solid var(--color-border)", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--color-text-secondary)" }}>
                CDSE Data Access Credentials
              </span>
            </div>
            <div style={{ padding: 20 }}>
              <div style={{ background: "var(--color-info-bg)", border: "1px solid var(--color-info-border)", borderRadius: 4, padding: "10px 14px", marginBottom: 16, fontSize: 12, color: "var(--color-info)" }}>
                <strong>Note:</strong> Credentials are stored in your <code style={{ fontFamily: "var(--font-mono)" }}>.env</code> file as{" "}
                <code style={{ fontFamily: "var(--font-mono)" }}>CDSE_USERNAME</code> and{" "}
                <code style={{ fontFamily: "var(--font-mono)" }}>CDSE_PASSWORD</code>.
                Register at{" "}
                <a href="https://dataspace.copernicus.eu" target="_blank" rel="noopener noreferrer" style={{ color: "var(--color-primary)" }}>
                  dataspace.copernicus.eu
                </a>.
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="settings-cdse-username">CDSE Username (Email)</label>
                <input
                  id="settings-cdse-username"
                  type="email"
                  className="form-input"
                  placeholder="your@email.com"
                  value={cdseUsername}
                  onChange={(e) => setCdseUsername(e.target.value)}
                  autoComplete="off"
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="settings-cdse-password">CDSE Password</label>
                <input
                  id="settings-cdse-password"
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={cdsePassword}
                  onChange={(e) => setCdsePassword(e.target.value)}
                  autoComplete="new-password"
                />
              </div>
            </div>
          </div>

          {/* Model Configuration */}
          <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, overflow: "hidden", marginBottom: 20 }}>
            <div style={{ padding: "10px 16px", background: "var(--color-surface-alt)", borderBottom: "1px solid var(--color-border)" }}>
              <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--color-text-secondary)" }}>
                Model Configuration
              </span>
            </div>
            <div style={{ padding: 20 }}>
              <div className="form-group">
                <label className="form-label" htmlFor="settings-model-path">Model Checkpoint Path</label>
                <input
                  id="settings-model-path"
                  type="text"
                  className="form-input"
                  placeholder="outputs/checkpoints/unet_best.pth"
                  value={modelPath}
                  onChange={(e) => setModelPath(e.target.value)}
                />
                <div style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: 4 }}>
                  Path relative to project root. Leave empty to run with random weights (development mode).
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="settings-cloud">
                  Default Max Cloud Cover: {cloudThreshold}%
                </label>
                <input
                  id="settings-cloud"
                  type="range"
                  min={0}
                  max={50}
                  step={5}
                  value={cloudThreshold}
                  onChange={(e) => setCloudThreshold(Number(e.target.value))}
                  className="form-input"
                  style={{ marginTop: 4 }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--color-text-muted)", marginTop: 2 }}>
                  <span>0% (Clear only)</span>
                  <span>50% (Moderate)</span>
                </div>
              </div>
            </div>
          </div>

          {/* System Info */}
          <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, overflow: "hidden", marginBottom: 20 }}>
            <div style={{ padding: "10px 16px", background: "var(--color-surface-alt)", borderBottom: "1px solid var(--color-border)" }}>
              <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--color-text-secondary)" }}>
                Platform Information
              </span>
            </div>
            <div style={{ padding: 4 }}>
              {[
                { label: "Platform", value: "GeoSentinel AI v1.0.0" },
                { label: "Study Area", value: "Hyderabad Metropolitan Region (HMR)" },
                { label: "Data Provider", value: "Copernicus Data Space Ecosystem (CDSE)" },
                { label: "Satellite", value: "Sentinel-2 Level-2A (10m resolution)" },
                { label: "Segmentation Model", value: "U-Net with ResNet34 encoder" },
                { label: "Coordinate System", value: "WGS84 / EPSG:4326" },
                { label: "Recommendation Engine", value: "Rule-based (YAML rules, no LLM)" },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: "flex", padding: "8px 16px", borderBottom: "1px solid var(--color-border)", fontSize: 12, gap: 12 }}>
                  <span style={{ fontWeight: 500, color: "var(--color-text-secondary)", minWidth: 180 }}>{label}</span>
                  <span style={{ color: "var(--color-text)", fontFamily: "var(--font-mono)", fontSize: 11 }}>{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Save button */}
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button type="submit" className="btn btn-primary" id="settings-save-btn">
              Save Settings
            </button>
            <a href="/" className="btn btn-ghost">Cancel</a>
            {saved && (
              <span style={{ fontSize: 12, color: "var(--color-success)", display: "flex", alignItems: "center", gap: 4 }}>
                ✓ Settings saved
              </span>
            )}
          </div>
        </form>
      </main>
    </div>
  );
}
