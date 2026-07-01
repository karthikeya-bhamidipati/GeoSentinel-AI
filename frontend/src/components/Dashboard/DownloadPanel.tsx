"use client";

// =============================================================================
// GeoSentinel AI — Download Panel
// =============================================================================

import { analysisApi } from "@/services/api";

interface DownloadPanelProps {
  jobId: string;
  outputs: Record<string, string>;
}

const DOWNLOAD_OPTIONS = [
  { key: "pdf", label: "PDF Report", icon: "📄" },
  { key: "csv", label: "Area Stats CSV", icon: "📊" },
  { key: "recommendations_csv", label: "Recommendations CSV", icon: "📋" },
  { key: "mask_png", label: "Land Cover Map", icon: "🗺️" },
  { key: "ndvi_delta_png", label: "NDVI Delta Map", icon: "🌿" },
];

export function DownloadPanel({ jobId, outputs }: DownloadPanelProps) {
  const available = DOWNLOAD_OPTIONS.filter((opt) => outputs[opt.key]);

  if (available.length === 0) return null;

  return (
    <div className="panel">
      <div className="panel-title">Download Reports</div>

      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {available.map((opt) => (
          <a
            key={opt.key}
            href={analysisApi.downloadUrl(jobId, opt.key)}
            download
            className="btn btn-ghost btn-sm"
            style={{
              justifyContent: "flex-start",
              gap: "8px",
              textDecoration: "none",
            }}
          >
            <span>{opt.icon}</span>
            <span>{opt.label}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
