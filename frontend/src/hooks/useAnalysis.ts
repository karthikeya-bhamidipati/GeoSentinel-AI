"use client";

// =============================================================================
// GeoSentinel AI — useAnalysis Hook
// =============================================================================

import { useState, useCallback, useRef } from "react";
import { analysisApi } from "@/services/api";
import type {
  AnalysisRequest,
  AnalysisResult,
  JobStatus,
} from "@/types";

interface AnalysisState {
  jobId: string | null;
  status: JobStatus | null;
  progressMessage: string;
  result: AnalysisResult | null;
  error: string | null;
  isLoading: boolean;
}

const INITIAL_STATE: AnalysisState = {
  jobId: null,
  status: null,
  progressMessage: "",
  result: null,
  error: null,
  isLoading: false,
};

const POLL_INTERVAL_MS = 3000;

/**
 * useAnalysis — manages the full analysis lifecycle.
 *
 * 1. Submits an analysis request to the API.
 * 2. Polls job status every 3 seconds.
 * 3. Fetches the full result when the job completes.
 * 4. Exposes loading state, progress messages, and errors.
 */
export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>(INITIAL_STATE);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const submit = useCallback(
    async (request: AnalysisRequest) => {
      setState({
        ...INITIAL_STATE,
        isLoading: true,
        progressMessage: "Submitting analysis ...",
      });

      try {
        // 1. Submit job
        const submitted = await analysisApi.submit(request);

        setState((prev) => ({
          ...prev,
          jobId: submitted.job_id,
          status: submitted.status,
          progressMessage: "Job queued ...",
        }));

        // 2. Start polling
        pollRef.current = setInterval(async () => {
          try {
            const statusResp = await analysisApi.getStatus(submitted.job_id);

            setState((prev) => ({
              ...prev,
              status: statusResp.status,
              progressMessage: statusResp.progress_message,
            }));

            if (statusResp.status === "completed") {
              stopPolling();

              // 3. Fetch result
              const result = await analysisApi.getResult(submitted.job_id);

              setState((prev) => ({
                ...prev,
                result,
                isLoading: false,
                progressMessage: "Analysis complete.",
              }));
            } else if (statusResp.status === "failed") {
              stopPolling();

              setState((prev) => ({
                ...prev,
                isLoading: false,
                error: statusResp.error ?? "Analysis failed.",
                progressMessage: "Failed.",
              }));
            }
          } catch (pollError) {
            // Network errors during polling are non-fatal
            console.warn("Polling error:", pollError);
          }
        }, POLL_INTERVAL_MS);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Submission failed.";

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: message,
          progressMessage: "Failed.",
        }));
      }
    },
    [stopPolling]
  );

  const reset = useCallback(() => {
    stopPolling();
    setState(INITIAL_STATE);
  }, [stopPolling]);

  return {
    ...state,
    submit,
    reset,
  };
}
