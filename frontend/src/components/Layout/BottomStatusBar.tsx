"use client";

// =============================================================================
// GeoSentinel AI — Bottom Status Bar
// Professional GIS-style status bar with coordinate display, CRS, zoom, and job status
// =============================================================================

import React, { useState, useEffect } from "react";
import type { JobStatus } from "@/types";

interface BottomStatusBarProps {
  status: JobStatus | null;
  message?: string;
  error?: string | null;
  zoom?: number;
}

export function BottomStatusBar({ status, message, error, zoom }: BottomStatusBarProps) {
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [time, setTime] = useState<string>("");

  // Update current time
  useEffect(() => {
    const update = () => {
      setTime(new Date().toUTCString().replace("GMT", "UTC").replace(" (Coordinated Universal Time)", ""));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  // Listen for coordinate events from the map
  useEffect(() => {
    const handler = (e: CustomEvent<{ lat: number; lng: number }>) => {
      setCoords(e.detail);
    };
    window.addEventListener("map:mousemove", handler as EventListener);
    return () => window.removeEventListener("map:mousemove", handler as EventListener);
  }, []);

  // Determine status dot state
  let dotClass = "idle";
  let statusText = "Ready";

  if (error) {
    dotClass = "error";
    statusText = `Error: ${error.length > 60 ? error.substring(0, 60) + "…" : error}`;
  } else if (status === "running" || status === "queued") {
    dotClass = "running";
    statusText = message || `${status.charAt(0).toUpperCase() + status.slice(1)}…`;
  } else if (status === "completed") {
    dotClass = "";  // green (default)
    statusText = "Analysis Complete";
  } else if (status === "failed") {
    dotClass = "error";
    statusText = "Analysis Failed";
  }

  return (
    <footer className="app-statusbar" role="status" aria-label="Application status bar" style={{ justifyContent: "center" }}>
      {/* Coordinates */}
      <div className="statusbar-item">
        {coords ? (
          <span>
            {coords.lat.toFixed(4)}°N, {coords.lng.toFixed(4)}°E
          </span>
        ) : (
          <span style={{ opacity: 0.5 }}>—°N, —°E</span>
        )}
      </div>

      {/* Zoom */}
      {zoom != null && (
        <>
          <div className="statusbar-divider" />
          <div className="statusbar-item">
            <span>Zoom: {zoom}</span>
          </div>
        </>
      )}
    </footer>
  );
}
