// =============================================================================
// GeoSentinel AI — TypeScript Types
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
      num_hotspots: number;
    };
  };
  statistics: Record<string, unknown>;
  recommendations: Recommendation[];
  outputs: Record<string, string>;
  metadata: {
    elapsed_seconds?: number;
    cloud_cover_t1?: number;
    cloud_cover_t2?: number;
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
  minLat: 16.8,
  minLng: 77.8,
  maxLat: 18.0,
  maxLng: 79.1,
};

export const HMR_CENTER: LatLng = {
  lat: 17.385,
  lng: 78.486,
};

// --------------------------------------------------------------------------
// Land Cover
// --------------------------------------------------------------------------

export const LAND_COVER_CLASSES: Record<
  number,
  { name: string; color: string }
> = {
  0: { name: "Background", color: "#000000" },
  1: { name: "Urban", color: "#DC143C" },
  2: { name: "Vegetation", color: "#228B22" },
  3: { name: "Water", color: "#1E90FF" },
  4: { name: "Barren", color: "#D2B48C" },
  5: { name: "Agriculture", color: "#FFD700" },
};
