"use client";

import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { PIPELINE_STEPS } from "@/types";

interface LogEntry {
  timestamp: string;
  message: string;
  step: string;
}

interface CyberTerminalProps {
  isVisible: boolean;
  progressMessage: string;
  progressSteps: string[];
  status: string;
  onClose: () => void;
  logs: LogEntry[];
}

export function CyberTerminal({ 
  isVisible, 
  progressMessage = "", 
  progressSteps = [], 
  status, 
  onClose, 
  logs 
}: CyberTerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  if (!isVisible) return null;

  const stepKeys = [
    "aoi",
    "search",
    "download",
    "preprocess",
    "features",
    "ai",
    "temporal",
    "area",
    "stats",
    "recommendations",
    "report"
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, x: "-50%", y: "-46%" }}
      animate={{ opacity: 1, scale: 1, x: "-50%", y: "-50%" }}
      exit={{ opacity: 0, scale: 0.96, x: "-50%", y: "-46%" }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="cyber-terminal"
      style={{
        position: "fixed",
        top: "50%",
        left: "50%",
        width: "540px",
        height: "320px",
        background: "rgba(10, 10, 15, 0.65)", // Premium semi-translucent glass
        backdropFilter: "var(--glass-blur)",
        WebkitBackdropFilter: "var(--glass-blur)",
        border: "1px solid rgba(255, 255, 255, 0.08)", // matches --color-border
        borderRadius: "var(--radius-xl)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        zIndex: 9999,
        boxShadow: "0 24px 64px rgba(0, 0, 0, 0.8), inset 0 0 20px rgba(255, 255, 255, 0.02)",
        fontFamily: "var(--font-mono)"
      }}
    >
      {/* Holographic style block */}
      <style>{`
        @keyframes pulse-glow {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; filter: brightness(1.2); }
        }
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(320px); }
        }
        .cyber-scanline {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 8px;
          background: linear-gradient(to bottom, transparent, rgba(255, 255, 255, 0.08), transparent);
          animation: scanline 4s linear infinite;
          pointer-events: none;
          z-index: 10;
        }
        .pulse-step {
          animation: pulse-glow 1s infinite alternate;
        }
        .cyber-close-btn:hover {
          background: rgba(255, 255, 255, 0.05) !important;
          color: #fff !important;
        }
      `}</style>

      {/* Holographic sweep laser line */}
      <div className="cyber-scanline" />

      {/* Tactical HUD Corner Brackets */}
      <div style={{ position: "absolute", top: 0, left: 0, width: 8, height: 8, borderTop: "2px solid rgba(255,255,255,0.4)", borderLeft: "2px solid rgba(255,255,255,0.4)", pointerEvents: "none", zIndex: 12 }} />
      <div style={{ position: "absolute", top: 0, right: 0, width: 8, height: 8, borderTop: "2px solid rgba(255,255,255,0.4)", borderRight: "2px solid rgba(255,255,255,0.4)", pointerEvents: "none", zIndex: 12 }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, width: 8, height: 8, borderBottom: "2px solid rgba(255,255,255,0.4)", borderLeft: "2px solid rgba(255,255,255,0.4)", pointerEvents: "none", zIndex: 12 }} />
      <div style={{ position: "absolute", bottom: 0, right: 0, width: 8, height: 8, borderBottom: "2px solid rgba(255,255,255,0.4)", borderRight: "2px solid rgba(255,255,255,0.4)", pointerEvents: "none", zIndex: 12 }} />

      {/* Terminal Header */}
      <div className="cyber-terminal-header" style={{
        background: "rgba(255, 255, 255, 0.02)",
        padding: "10px 14px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
        position: "relative",
        zIndex: 11
      }}>
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
          {/* Pulsing indicator lights */}
          <div style={{ 
            width: 8, 
            height: 8, 
            borderRadius: "50%", 
            background: "#f87171",
            opacity: status === "failed" ? 1 : 0.4,
            boxShadow: status === "failed" ? "0 0 8px #f87171" : "none"
          }} />
          <div style={{ 
            width: 8, 
            height: 8, 
            borderRadius: "50%", 
            background: "#fbbf24",
            opacity: status === "queued" ? 1 : 0.4,
            boxShadow: status === "queued" ? "0 0 8px #fbbf24" : "none"
          }} />
          <div style={{ 
            width: 8, 
            height: 8, 
            borderRadius: "50%", 
            background: "#34d399",
            opacity: status === "running" ? 1 : (status === "completed" ? 0.8 : 0.4),
            animation: status === "running" ? "pulse-glow 0.8s infinite alternate" : "none",
            boxShadow: status === "running" || status === "completed" ? "0 0 10px #34d399" : "none"
          }} />
        </div>
        <div style={{ color: "rgba(255, 255, 255, 0.8)", fontSize: "10px", fontWeight: 600, letterSpacing: "1.5px", textTransform: "uppercase" }}>
          Pipeline Diagnostics // {status}
        </div>
        <button onClick={onClose} className="cyber-close-btn" style={{ 
          background: "transparent", 
          border: "none", 
          color: "rgba(255,255,255,0.4)", 
          cursor: "pointer", 
          fontSize: "12px",
          width: "20px",
          height: "20px",
          borderRadius: "4px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.2s"
        }}>✕</button>
      </div>

      {/* LED HUD Progress Segments */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "4px",
        padding: "8px 14px",
        background: "rgba(0, 0, 0, 0.4)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
        position: "relative",
        zIndex: 5
      }}>
        {stepKeys.map((stepKey) => {
          const isCompleted = progressSteps.includes(stepKey) && (progressSteps.indexOf(stepKey) < progressSteps.length - 1 || status !== "running");
          const isActive = progressSteps.includes(stepKey) && progressSteps.indexOf(stepKey) === progressSteps.length - 1 && status === "running";
          const stepInfo = PIPELINE_STEPS[stepKey] || { label: stepKey, color: "#64748b" };

          return (
            <div 
              key={stepKey} 
              title={`${stepInfo.label}: ${isActive ? "ACTIVE" : isCompleted ? "COMPLETED" : "QUEUED"}`}
              style={{
                flex: 1,
                height: "4px",
                borderRadius: "1px",
                background: isCompleted 
                  ? stepInfo.color 
                  : isActive 
                    ? "#ffffff"
                    : "rgba(255, 255, 255, 0.08)",
                boxShadow: isCompleted 
                  ? `0 0 6px ${stepInfo.color}` 
                  : isActive 
                    ? `0 0 10px #ffffff` 
                    : "none",
                transition: "all 0.3s ease",
              }}
              className={isActive ? "pulse-step" : undefined}
            />
          );
        })}
      </div>

      {/* Progress Message */}
      <div style={{
        padding: "6px 14px",
        background: "rgba(0, 0, 0, 0.2)",
        fontSize: "10px",
        color: "#cbd5e1",
        borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "80%" }}>
          <span style={{ color: "rgba(255, 255, 255, 0.4)", fontWeight: 700 }}>&gt;</span>
          <span style={{ opacity: 0.9 }}>{progressMessage || (status === "running" ? "Initializing..." : "Ready")}</span>
        </div>
        <div style={{ opacity: 0.5, fontSize: "9px", flexShrink: 0 }}>
          {progressSteps.length}/{stepKeys.length} STEPS
        </div>
      </div>
      
      {/* Logs Window */}
      <div ref={scrollRef} className="cyber-terminal-body" style={{
        flex: 1,
        overflowY: "auto",
        padding: "12px 14px",
        display: "flex",
        flexDirection: "column",
        gap: "4px"
      }}>
        {logs.map((log, i) => {
          const stepInfo = PIPELINE_STEPS[log.step] || { label: "SYSTEM", color: "#64748b" };
          return (
            <div key={i} className="cyber-terminal-line" style={{ display: "flex", fontSize: "11px", gap: "6px", lineHeight: "1.4" }}>
              <span className="timestamp" style={{ color: "rgba(255, 255, 255, 0.35)", fontSize: "10px" }}>[{log.timestamp}]</span>
              <span className="step-tag" style={{ color: stepInfo.color, minWidth: "90px", fontSize: "10.5px", fontWeight: 600 }}>[{stepInfo.label.toUpperCase()}]</span>
              <span style={{ color: "var(--color-text-secondary)" }}>{log.message}</span>
            </div>
          );
        })}
        {status === "running" && (
          <div className="cyber-terminal-line" style={{ display: "flex", fontSize: "11px", gap: "6px", marginTop: "2px" }}>
            <span style={{ color: "rgba(255, 255, 255, 0.35)" }}>[SYS]</span>
            <span style={{ color: "var(--color-text-secondary)" }}>&gt;</span>
            <motion.span 
              animate={{ opacity: [1, 0] }} 
              transition={{ repeat: Infinity, duration: 0.8 }}
              style={{ width: "6px", height: "12px", background: "rgba(255,255,255,0.7)", display: "inline-block", marginLeft: "4px" }}
            />
          </div>
        )}
      </div>
    </motion.div>
  );
}
