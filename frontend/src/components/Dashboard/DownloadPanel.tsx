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
  { key: "image_t1_png", label: "T1 True-Color Image (.png)", icon: "🛰️" },
  { key: "image_t2_png", label: "T2 True-Color Image (.png)", icon: "🛰️" },
  { key: "mask_t1_png", label: "T1 Land Cover Mask (.png)", icon: "🗺️" },
  { key: "mask_t2_png", label: "T2 Land Cover Mask (.png)", icon: "🗺️" },
  { key: "mask_t1", label: "T1 Land Cover Mask (.tif)", icon: "🗺️" },
  { key: "mask_t2", label: "T2 Land Cover Mask (.tif)", icon: "🗺️" },
  { key: "ndvi_delta_png", label: "NDVI Delta Map (.png)", icon: "🌿" },
  { key: "ndbi_delta_png", label: "NDBI Delta Map (.png)", icon: "🏢" },
  { key: "ndvi_delta_tif", label: "NDVI Delta (.tif)", icon: "🌿" },
  { key: "ndbi_delta_tif", label: "NDBI Delta (.tif)", icon: "🏢" },
  { key: "pdf", label: "PDF Report (.pdf)", icon: "📄" },
  { key: "csv", label: "Area Stats (.csv)", icon: "📊" },
  { key: "recommendations_csv", label: "Recommendations (.csv)", icon: "📋" },
  { key: "hotspots_geojson", label: "Change Hotspots (.geojson)", icon: "📍" },
  { key: "aoi_geojson", label: "AOI (.geojson)", icon: "📍" },
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
