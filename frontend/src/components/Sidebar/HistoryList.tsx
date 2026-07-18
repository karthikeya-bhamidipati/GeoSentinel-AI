import React, { useEffect, useState } from "react";
import { analysisApi } from "@/services/api";
import { Trash2 } from "lucide-react";

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

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to permanently delete this analysis?")) return;
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analysis/${jobId}`, {
        method: "DELETE"
      });
      fetchHistory(); // Refresh the list
    } catch (err) {
      console.error("Failed to delete job", err);
    }
  };

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
      <div className="form-section-title" style={{ marginBottom: "var(--space-3)", fontSize: "14px", fontWeight: 600 }}>Past Analyses</div>
      {history.map((job) => (
        <div 
          key={job.job_id} 
          className="layer-item" 
          style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            alignItems: "center", 
            padding: "12px", 
            marginBottom: "12px", 
            cursor: job.status === "completed" ? "pointer" : "default",
            background: "var(--color-surface-glass)",
            border: "1px solid var(--color-border)",
            borderRadius: "8px",
            transition: "all 0.2s"
          }}
          onClick={() => {
            if (job.status === "completed" && job.result && onLoadHistory) {
              onLoadHistory(job.result);
            }
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", width: "100%", fontSize: "12px", fontWeight: 600 }}>
              <span style={{ color: "var(--color-text)" }}>
                {job.result ? `${job.result.date1} → ${job.result.date2}` : job.job_id.split("-")[0]}
              </span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>
              {new Date(job.created_at).toLocaleString()}
              <span style={{ 
                marginLeft: "8px",
                color: job.status === "completed" ? "var(--color-success)" : job.status === "failed" ? "var(--color-error)" : "var(--color-warning)",
                textTransform: "capitalize",
                fontWeight: 600
              }}>
                • {job.status}
              </span>
            </div>
          </div>
          <button 
            onClick={(e) => handleDelete(e, job.job_id)}
            style={{ 
              background: "transparent", 
              border: "none", 
              color: "var(--color-text-muted)", 
              cursor: "pointer",
              padding: "4px"
            }}
            title="Delete analysis"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}

