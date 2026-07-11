import React, { useEffect, useState } from "react";
import { analysisApi } from "@/services/api";

interface HistoryJob {
  job_id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  error?: string;
  result?: any;
}

interface HistoryListProps {
  onLoadHistory?: (job: any) => void;
}

export function HistoryList({ onLoadHistory }: HistoryListProps) {
  const [history, setHistory] = useState<HistoryJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchHistory() {
      setIsLoading(true);
      try {
        const data = await analysisApi.getHistory();
        setHistory(data.jobs || []);
      } catch (err) {
        console.error("Failed to fetch history", err);
      } finally {
        setIsLoading(false);
      }
    }
    
    fetchHistory();
  }, []);

  if (isLoading) {
    return (
      <div style={{ padding: "1rem" }}>
        <div className="skeleton-title" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton-row">
              <div className="skeleton-line skeleton-line-md" />
              <div className="skeleton-line skeleton-line-sm" />
            </div>
            <div className="skeleton-line skeleton-line-lg" style={{ marginTop: 6 }} />
          </div>
        ))}
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="empty-state" style={{ paddingTop: "var(--space-8)" }}>
        <p className="empty-state-title">No History Available</p>
        <p className="empty-state-text">Run your first analysis to see it here.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="form-section-title" style={{ marginBottom: "var(--space-3)" }}>Past Analyses</div>
      {history.map((job) => (
        <div 
          key={job.job_id} 
          className="layer-item" 
          style={{ 
            display: "flex", 
            flexDirection: "column", 
            alignItems: "flex-start", 
            gap: "4px", 
            padding: "8px", 
            marginBottom: "8px", 
            cursor: job.status === "completed" ? "pointer" : "default",
            background: "var(--color-surface-alt)",
            border: "1px solid var(--color-border)",
            borderRadius: "4px"
          }}
          onClick={() => {
            if (job.status === "completed" && job.result && onLoadHistory) {
              onLoadHistory(job.result);
            }
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", width: "100%", fontSize: "0.8rem", fontWeight: 600 }}>
            <span style={{ color: "var(--color-text)" }}>
              {job.result ? `${job.result.date1} → ${job.result.date2}` : job.job_id.split("-")[0]}
            </span>
            <span style={{ 
              color: job.status === "completed" ? "var(--color-green)" : job.status === "failed" ? "var(--color-danger)" : "var(--color-accent)",
              textTransform: "capitalize",
              fontSize: "0.7rem"
            }}>
              {job.status}
            </span>
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--color-text-muted)" }}>
            {new Date(job.created_at).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
