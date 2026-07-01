"use client";

// =============================================================================
// GeoSentinel AI — Statistics Panel
// =============================================================================

interface StatisticsPanelProps {
  temporalStats: {
    ndvi_change?: {
      mean_delta: number;
      gain_pct: number;
      loss_pct: number;
    };
    ndbi_change?: {
      mean_delta: number;
      urban_increase_pct: number;
    };
    segmentation_change?: {
      changed_pct: number;
      num_hotspots: number;
    };
  };
}

export function StatisticsPanel({ temporalStats }: StatisticsPanelProps) {
  const ndvi = temporalStats.ndvi_change;
  const ndbi = temporalStats.ndbi_change;
  const seg = temporalStats.segmentation_change;

  if (!ndvi && !ndbi && !seg) return null;

  return (
    <div className="panel">
      <div className="panel-title">Temporal Statistics</div>

      <div className="stat-grid">
        {ndvi && (
          <>
            <div className="stat-item">
              <div className="stat-label">NDVI Change</div>
              <div
                className={`stat-value ${
                  ndvi.mean_delta >= 0 ? "positive" : "negative"
                }`}
              >
                {ndvi.mean_delta >= 0 ? "+" : ""}
                {ndvi.mean_delta.toFixed(3)}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Veg. Loss</div>
              <div className="stat-value negative">
                {ndvi.loss_pct.toFixed(1)}%
              </div>
            </div>
          </>
        )}

        {ndbi && (
          <>
            <div className="stat-item">
              <div className="stat-label">NDBI Change</div>
              <div
                className={`stat-value ${
                  ndbi.mean_delta >= 0 ? "negative" : "positive"
                }`}
              >
                {ndbi.mean_delta >= 0 ? "+" : ""}
                {ndbi.mean_delta.toFixed(3)}
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Urban Growth</div>
              <div className="stat-value negative">
                {ndbi.urban_increase_pct.toFixed(1)}%
              </div>
            </div>
          </>
        )}

        {seg && (
          <>
            <div className="stat-item">
              <div className="stat-label">Changed Area</div>
              <div className="stat-value">
                {seg.changed_pct.toFixed(1)}%
              </div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Hotspots</div>
              <div
                className={`stat-value ${
                  seg.num_hotspots > 0 ? "negative" : "positive"
                }`}
              >
                {seg.num_hotspots}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
