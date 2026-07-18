"use client";

import React from "react";
import { Eye, Play, Pause } from "lucide-react";

interface BlinkModeProps {
  isActive: boolean;
  onToggle: () => void;
  currentFrame: 'T1' | 'T2';
  speed: number;
  onSpeedChange: (speed: number) => void;
}

export function BlinkMode({ isActive, onToggle, currentFrame, speed, onSpeedChange }: BlinkModeProps) {
  return (
    <div className="blink-toggle" style={{ 
      position: "absolute", 
      bottom: 70, 
      left: "calc(50% + (var(--sidebar-icon-width) + var(--sidebar-panel-width) - var(--right-panel-width)) / 2)", 
      transform: "translateX(-50%)",
      zIndex: 1000, 
      background: "var(--color-surface-glass)", 
      backdropFilter: "var(--glass-blur)", 
      WebkitBackdropFilter: "var(--glass-blur)",
      padding: "10px 20px", 
      borderRadius: "30px", 
      border: "1px solid var(--color-border)",
      boxShadow: "var(--shadow-lg)",
      display: "flex",
      alignItems: "center",
      gap: "24px"
    }}>
      <button onClick={onToggle} style={{ 
        background: "transparent", 
        border: "none", 
        color: isActive ? "var(--color-error)" : "var(--color-text)", 
        cursor: "pointer", 
        display: "flex", 
        alignItems: "center", 
        gap: "8px",
        outline: "none"
      }}>
        {isActive ? <Pause size={24} /> : <Eye size={24} />}
        <span style={{ fontWeight: 600, fontSize: "14px", textTransform: "uppercase", letterSpacing: "1px" }}>
          {isActive ? "Stop Blink" : "Blink Mode"}
        </span>
      </button>

      {isActive && (
        <>
          <div style={{ 
            color: "#0f172a", 
            fontWeight: "bold", 
            padding: "4px 12px", 
            background: currentFrame === 'T1' ? "#34d399" : "#38bdf8", 
            borderRadius: "12px",
            fontSize: "14px",
            transition: "background 0.2s"
          }}>
            FRAME: {currentFrame}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ color: "#94a3b8", fontSize: "12px", fontWeight: 600 }}>{speed}ms</span>
            <input 
              type="range" 
              min="100" 
              max="1500" 
              step="100" 
              value={speed} 
              onChange={(e) => onSpeedChange(Number(e.target.value))} 
              style={{ width: "100px", accentColor: "#38bdf8" }}
            />
          </div>
        </>
      )}
    </div>
  );
}
