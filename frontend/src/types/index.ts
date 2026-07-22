// =============================================================================
// GeoSentinel AI — TypeScript Types (v2.0)
// =============================================================================

export type JobStatus = "queued" | "running" | "completed" | "failed";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

// --------------------------------------------------------------------------
// API Requests
// --------------------------------------------------------------------------

export interface AOIGeometry {
  type: string;
  coordinates: number[][][] | number[][];
}

export interface AnalysisRequest {
  aoi: AOIGeometry;
  date1: string;
  date2: string;
  max_cloud_cover?: number;
}

// --------------------------------------------------------------------------
// API Responses
// --------------------------------------------------------------------------

export interface JobSubmitted {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress_message: string;
  progress_steps: string[];
  created_at?: string;
  completed_at?: string;
  error?: string;
}

export interface AreaStatRow {
  class_id: number;
  class_name: string;
  t1_area_km2: number;
  t2_area_km2: number;
  t1_pct: number;
  t2_pct: number;
  change_km2: number;
  change_pct: number;
}

export interface Recommendation {
  rule_id: string;
  category: string;
  severity: Severity;
  title: string;
  recommendation: string;
  why: string;
  priority: number;
}

export interface AnalysisResult {
  job_id: string;
  success: boolean;
  date1: string;
  date2: string;
  scene_t1_id: string;
  scene_t2_id: string;
  area_change: {
    rows: AreaStatRow[];
    total_area_km2: number;
  };
  temporal_stats: {
    ndvi_change?: {
      mean_delta: number;
      gain_pct: number;
      loss_pct: number;
      stable_pct: number;
    };
    ndbi_change?: {
      mean_delta: number;
      urban_increase_pct: number;
    };
    segmentation_change?: {
      changed_pct: number;
      urban_expansion_pixels: number;
      vegetation_loss_pixels: number;
      water_loss_pixels: number;
      num_hotspots: number;
      hotspots?: Array<{
        center_row: number;
        center_col: number;
        center_lat: number | null;
        center_lon: number | null;
        area_pixels: number;
        from_class: string;
        to_class: string;
      }>;
      transition_matrix?: Record<string, Record<string, number>>;
    };
  };
  statistics: Record<string, unknown>;
  recommendations: Recommendation[];
  outputs: Record<string, string>;
  metadata: {
    elapsed_seconds?: number;
    date1?: string;
    date2?: string;
    seasonal_shift?: boolean;
    scene_t1_id?: string;
    scene_t2_id?: string;
    cloud_cover_t1?: number;
    cloud_cover_t2?: number;
    acquisition_date_t1?: string;
    acquisition_date_t2?: string;
    cloud_mask_t1_pct?: number;
    cloud_mask_t2_pct?: number;
    preprocessing_steps?: string[];
    crs?: string;
    pixel_resolution_m?: number;
    bbox?: number[];
  };
  error?: string;
}

// --------------------------------------------------------------------------
// Map
// --------------------------------------------------------------------------

export interface LatLng {
  lat: number;
  lng: number;
}

export interface MapBounds {
  minLat: number;
  minLng: number;
  maxLat: number;
  maxLng: number;
}

// HMR bounding box (Hyderabad Metropolitan Region)
export const HMR_BOUNDS: MapBounds = {
  minLat: 15.44,
  minLng: 76.38,
  maxLat: 19.36,
  maxLng: 80.52,
};

export const HMR_CENTER: LatLng = {
  lat: 17.385,
  lng: 78.486,
};

// --------------------------------------------------------------------------
// Land Cover — Neon glow palette for dark theme
// --------------------------------------------------------------------------

export const LAND_COVER_CLASSES: Record<
  number,
  { name: string; color: string }
> = {
  0: { name: "Background", color: "#1e293b" },
  1: { name: "Urban",      color: "#f87171" },
  2: { name: "Vegetation", color: "#34d399" },
  3: { name: "Water",      color: "#38bdf8" },
  4: { name: "Barren",     color: "#d97706" }
};

// --------------------------------------------------------------------------
// Pipeline Steps (for CyberTerminal display)
// --------------------------------------------------------------------------

export const PIPELINE_STEPS: Record<string, { label: string; color: string }> = {
  aoi:              { label: "AOI",             color: "#a78bfa" },
  search:           { label: "STAC Search",     color: "#38bdf8" },
  download:         { label: "Download",        color: "#60a5fa" },
  preprocess:       { label: "Preprocess",      color: "#fbbf24" },
  features:         { label: "Features",        color: "#fb923c" },
  ai:               { label: "AI Model",        color: "#f472b6" },
  temporal:         { label: "Temporal",         color: "#34d399" },
  area:             { label: "Area Stats",       color: "#2dd4bf" },
  stats:            { label: "Statistics",       color: "#6ee7b7" },
  recommendations:  { label: "Recommendations", color: "#fbbf24" },
  report:           { label: "Report",          color: "#a3e635" },
};

// --------------------------------------------------------------------------
// Severity styling
// --------------------------------------------------------------------------

export const SEVERITY_CONFIG: Record<Severity, { color: string; bg: string; label: string }> = {
  CRITICAL: { color: "#f87171", bg: "rgba(248, 113, 113, 0.15)", label: "Critical" },
  HIGH:     { color: "#fb923c", bg: "rgba(251, 146, 60, 0.15)",  label: "High" },
  MEDIUM:   { color: "#fbbf24", bg: "rgba(251, 191, 36, 0.15)",  label: "Medium" },
  LOW:      { color: "#34d399", bg: "rgba(52, 211, 153, 0.15)",  label: "Low" },
};
