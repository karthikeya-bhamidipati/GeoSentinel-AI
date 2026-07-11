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
  progressSteps: string[];
  result: AnalysisResult | null;
  error: string | null;
  isLoading: boolean;
}

const INITIAL_STATE: AnalysisState = {
  jobId: null,
  status: null,
  progressMessage: "",
  progressSteps: [],
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
  const wsRef = useRef<WebSocket | null>(null);

  const stopPolling = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
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
          progressSteps: [],
        }));

        // 2. Start WebSocket
        const wsUrl = process.env.NEXT_PUBLIC_API_URL
          ? `${process.env.NEXT_PUBLIC_API_URL.replace(/^http/, "ws")}/api/v1/analysis/${submitted.job_id}/ws`
          : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/v1/analysis/${submitted.job_id}/ws`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = async (event) => {
          try {
            const statusResp = JSON.parse(event.data);

            setState((prev) => ({
              ...prev,
              status: statusResp.status,
              progressMessage: statusResp.progress_message,
              progressSteps: statusResp.progress_steps ?? [],
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
                progressSteps: statusResp.progress_steps ?? prev.progressSteps,
              }));
            } else if (statusResp.status === "failed") {
              stopPolling();
              setState((prev) => ({
                ...prev,
                isLoading: false,
                error: statusResp.error ?? "Analysis failed.",
                progressMessage: "Failed.",
                progressSteps: statusResp.progress_steps ?? prev.progressSteps,
              }));
            }
          } catch (wsError) {
            console.warn("WebSocket message error:", wsError);
          }
        };

        ws.onerror = (err) => console.warn("WebSocket error:", err);
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

  const setResult = useCallback((result: AnalysisResult) => {
    setState({
      ...INITIAL_STATE,
      result,
    });
  }, []);

  return {
    ...state,
    submit,
    reset,
    setResult,
  };
}
