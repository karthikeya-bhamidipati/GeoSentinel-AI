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

export function CyberTerminal({ isVisible, status, onClose, logs }: CyberTerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 50 }}
      className="cyber-terminal"
      style={{
        position: "absolute",
        top: "calc(var(--gap) * 2 + var(--header-height))",
        bottom: "var(--gap)",
        right: "var(--gap)",
        width: "var(--right-panel-width)",
        background: "var(--color-surface)",
        backdropFilter: "var(--glass-blur)",
        WebkitBackdropFilter: "var(--glass-blur)",
        border: "1px solid var(--color-border)",
        borderLeft: "1px solid var(--color-primary-border)",
        borderRadius: "var(--radius-md)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        zIndex: 2000,
        boxShadow: "-4px 0 24px rgba(0,0,0,0.5), 0 0 20px rgba(56,189,248,0.1)",
        fontFamily: "var(--font-mono)"
      }}
    >
      <div className="cyber-terminal-header" style={{
        background: "var(--color-surface-alt)",
        padding: "12px 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid var(--color-border)"
      }}>
        <div style={{ display: "flex", gap: "6px" }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#f87171" }}></div>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#fbbf24" }}></div>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#34d399" }}></div>
        </div>
        <div style={{ color: "#94a3b8", fontSize: "11px", fontWeight: 600, letterSpacing: "1px" }}>
          GEOSENTINEL_PIPELINE_V2 // {status.toUpperCase()}
        </div>
        <button onClick={onClose} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", fontSize: "14px" }}>✕</button>
      </div>
      
      <div ref={scrollRef} className="cyber-terminal-body" style={{
        flex: 1,
        overflowY: "auto",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "6px"
      }}>
        {logs.map((log, i) => {
          const stepInfo = PIPELINE_STEPS[log.step] || { label: "SYSTEM", color: "#64748b" };
          return (
            <div key={i} className="cyber-terminal-line" style={{ display: "flex", fontSize: "12px", gap: "8px" }}>
              <span className="timestamp" style={{ color: "#0ea5e9", opacity: 0.8 }}>[{log.timestamp}]</span>
              <span className="step-tag" style={{ color: stepInfo.color, minWidth: "90px" }}>&lt;{stepInfo.label}&gt;</span>
              <span style={{ color: "#e2e8f0" }}>{log.message}</span>
            </div>
          );
        })}
        {status === "running" && (
          <div className="cyber-terminal-line" style={{ display: "flex", fontSize: "12px", gap: "8px", marginTop: "4px" }}>
            <span style={{ color: "#0ea5e9", opacity: 0.8 }}>[SYS]</span>
            <span style={{ color: "#38bdf8" }}>&gt;</span>
            <motion.span 
              animate={{ opacity: [1, 0] }} 
              transition={{ repeat: Infinity, duration: 0.8 }}
              style={{ width: "8px", height: "14px", background: "#38bdf8", display: "inline-block" }}
            />
          </div>
        )}
      </div>
    </motion.div>
  );
}
