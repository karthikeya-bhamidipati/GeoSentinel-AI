"use client";

// =============================================================================
// GeoSentinel AI — useAnalysis Hook (v2.0)
// Enhanced with log history for CyberTerminal
// =============================================================================

import { useState, useCallback, useRef } from "react";
import { analysisApi } from "@/services/api";
import type {
  AnalysisRequest,
  AnalysisResult,
  JobStatus,
} from "@/types";

export interface LogEntry {
  timestamp: string;
  message: string;
  step: string;
}

interface AnalysisState {
  jobId: string | null;
  status: JobStatus | null;
  progressMessage: string;
  progressSteps: string[];
  result: AnalysisResult | null;
  error: string | null;
  isLoading: boolean;
  logs: LogEntry[];
}

const INITIAL_STATE: AnalysisState = {
  jobId: null,
  status: null,
  progressMessage: "",
  progressSteps: [],
  result: null,
  error: null,
  isLoading: false,
  logs: [],
};

/**
 * useAnalysis — manages the full analysis lifecycle.
 *
 * 1. Submits an analysis request to the API.
 * 2. Opens a WebSocket for real-time progress updates.
 * 3. Accumulates log entries for the CyberTerminal.
 * 4. Fetches the full result when the job completes.
 * 5. Exposes loading state, progress messages, logs, and errors.
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
      const startLog: LogEntry = {
        timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
        message: "Initializing GeoSentinel Pipeline v2.0 ...",
        step: "init",
      };

      setState({
        ...INITIAL_STATE,
        isLoading: true,
        progressMessage: "Submitting analysis ...",
        logs: [startLog],
      });

      try {
        // 1. Submit job
        const submitted = await analysisApi.submit(request);

        const submitLog: LogEntry = {
          timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
          message: `Job created: ${submitted.job_id}`,
          step: "init",
        };

        setState((prev) => ({
          ...prev,
          jobId: submitted.job_id,
          status: submitted.status,
          progressMessage: "Job queued ...",
          progressSteps: [],
          logs: [...prev.logs, submitLog],
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

            // Build a new log entry from the progress message
            const currentStep =
              statusResp.progress_steps?.length > 0
                ? statusResp.progress_steps[statusResp.progress_steps.length - 1]
                : "system";

            const newLog: LogEntry = {
              timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
              message: statusResp.progress_message || statusResp.status,
              step: currentStep,
            };

            setState((prev) => {
              // Avoid duplicate log entries
              const lastLog = prev.logs[prev.logs.length - 1];
              const isDuplicate = lastLog && lastLog.message === newLog.message;
              const updatedLogs = isDuplicate ? prev.logs : [...prev.logs, newLog];

              return {
                ...prev,
                status: statusResp.status,
                progressMessage: statusResp.progress_message,
                progressSteps: statusResp.progress_steps ?? [],
                logs: updatedLogs,
              };
            });

            if (statusResp.status === "completed") {
              stopPolling();
              // 3. Fetch result
              const result = await analysisApi.getResult(submitted.job_id);

              const completeLog: LogEntry = {
                timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
                message: "✓ Pipeline execution complete. All outputs generated.",
                step: "done",
              };

              setState((prev) => ({
                ...prev,
                result,
                isLoading: false,
                progressMessage: "Analysis complete.",
                progressSteps: statusResp.progress_steps ?? prev.progressSteps,
                logs: [...prev.logs, completeLog],
              }));
            } else if (statusResp.status === "failed") {
              stopPolling();

              const failLog: LogEntry = {
                timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
                message: `✕ Pipeline failed: ${statusResp.error ?? "Unknown error"}`,
                step: "error",
              };

              setState((prev) => ({
                ...prev,
                isLoading: false,
                error: statusResp.error ?? "Analysis failed.",
                progressMessage: "Failed.",
                progressSteps: statusResp.progress_steps ?? prev.progressSteps,
                logs: [...prev.logs, failLog],
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

        const errorLog: LogEntry = {
          timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
          message: `✕ ${message}`,
          step: "error",
        };

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: message,
          progressMessage: "Failed.",
          logs: [...prev.logs, errorLog],
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

  const clearLogs = useCallback(() => {
    setState((prev) => ({ ...prev, logs: [] }));
  }, []);

  return {
    ...state,
    submit,
    reset,
    setResult,
    clearLogs,
  };
}
