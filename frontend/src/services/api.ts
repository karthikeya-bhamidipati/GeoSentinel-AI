// =============================================================================
// GeoSentinel AI — API Service
// =============================================================================

import type {
  AnalysisRequest,
  AnalysisResult,
  JobStatusResponse,
  JobSubmitted,
} from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
    : "/api/v1";

// --------------------------------------------------------------------------
// Fetch Helper
// --------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail ?? `API error: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}

// --------------------------------------------------------------------------
// Analysis API
// --------------------------------------------------------------------------

export const analysisApi = {
  /**
   * Submit a new analysis job.
   */
  submit: async (request: AnalysisRequest): Promise<JobSubmitted> =>
    apiFetch<JobSubmitted>("/analysis", {
      method: "POST",
      body: JSON.stringify(request),
    }),

  /**
   * Poll the status of a job.
   */
  getStatus: async (jobId: string): Promise<JobStatusResponse> =>
    apiFetch<JobStatusResponse>(`/analysis/${jobId}`),

  /**
   * Fetch the completed result of a job.
   */
  getResult: async (jobId: string): Promise<AnalysisResult> =>
    apiFetch<AnalysisResult>(`/analysis/${jobId}/result`),

  /**
   * Get the download URL for a report file.
   */
  downloadUrl: (jobId: string, fileType: string): string =>
    `${API_BASE}/download/${jobId}/${fileType}`,
};

// --------------------------------------------------------------------------
// Boundary API
// --------------------------------------------------------------------------

export const boundaryApi = {
  /**
   * Fetch the HMR boundary GeoJSON.
   */
  getHMRBoundary: async (): Promise<GeoJSON.FeatureCollection> =>
    apiFetch<GeoJSON.FeatureCollection>("/boundary"),
};

// --------------------------------------------------------------------------
// Health API
// --------------------------------------------------------------------------

export const healthApi = {
  check: async () =>
    apiFetch<{ status: string; version: string }>("/health"),
};
