// =============================================================================
// GeoSentinel AI — Benchmark Page
// OSCD change-detection results for the released checkpoints
// (values generated from outputs/oscd/summary.json into src/data/benchmarkResults.ts)
// =============================================================================

import type { Metadata } from "next";
import { CHANGE_RESULTS, LAND_COVER, PROTOCOL } from "@/data/benchmarkResults";

export const metadata: Metadata = {
  title: "Model Benchmark — GeoSentinel AI",
  description: "OSCD change-detection results of the Semantically-Anchored Linear Attention Siamese U-Net and its ImageNet-initialised baseline.",
};

const pm = (m: { mean: number; sd: number }) => `${m.mean.toFixed(2)} ± ${m.sd.toFixed(2)}`;

export default function BenchmarkPage() {
  const [proposed, baseline] = CHANGE_RESULTS;
  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)", fontFamily: "var(--font-sans)", color: "var(--color-text)" }}>
      <header style={{ background: "var(--color-header)", color: "white", padding: "0 32px", height: 48, display: "flex", alignItems: "center", gap: 12 }}>
        <a href="/" style={{ color: "rgba(255,255,255,0.6)", textDecoration: "none", fontSize: 12 }}>← GeoSentinel AI</a>
        <span style={{ color: "rgba(255,255,255,0.3)", fontSize: 12 }}>/</span>
        <span style={{ fontSize: 14, fontWeight: 600, color: "white" }}>Model Benchmark</span>
      </header>

      <main style={{ maxWidth: 960, margin: "0 auto", padding: "32px 24px" }}>
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--color-text)", marginBottom: 6 }}>
            Change Detection Benchmark (OSCD)
          </h1>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)", lineHeight: 1.6 }}>
            Full-scene evaluation on the ten OSCD test cities (pooled confusion matrix, τ = 0.5), mean ± standard
            deviation over {PROTOCOL.seeds} training seeds. Checkpoints were selected on held-out training cities only.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 24 }}>
          {[
            { label: "Proposed F1", value: pm(proposed.f1), sub: "OSCD test cities, %" },
            { label: "Difference vs baseline", value: `${(proposed.f1.mean - baseline.f1.mean).toFixed(2)} pts`, sub: "F1, identical architecture" },
            { label: "Parameters", value: proposed.params, sub: "trainable (both models)" },
          ].map(({ label, value, sub }) => (
            <div key={label} style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, padding: "16px 16px" }}>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--color-text-muted)", marginBottom: 6 }}>{label}</div>
              <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--color-text)" }}>{value}</div>
              <div style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: 2 }}>{sub}</div>
            </div>
          ))}
        </div>

        <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, overflow: "hidden", marginBottom: 24 }}>
          <div style={{ padding: "10px 16px", background: "var(--color-surface-alt)", borderBottom: "1px solid var(--color-border)" }}>
            <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--color-text-secondary)" }}>
              Change detection (OSCD, %)
            </span>
          </div>
          <table className="benchmark-table" style={{ width: "100%" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}>Model</th>
                <th>OA</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1 ↑</th>
                <th>IoU</th>
              </tr>
            </thead>
            <tbody>
              {CHANGE_RESULTS.map((r, i) => (
                <tr key={r.model}>
                  <td style={{ fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 13 }}>{r.model}</td>
                  <td>{pm(r.oa)}</td>
                  <td>{pm(r.precision)}</td>
                  <td>{pm(r.recall)}</td>
                  <td className={i === 0 ? "benchmark-best" : ""}>{pm(r.f1)}</td>
                  <td>{pm(r.iou)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, overflow: "hidden", marginBottom: 24 }}>
          <div style={{ padding: "10px 16px", background: "var(--color-surface-alt)", borderBottom: "1px solid var(--color-border)" }}>
            <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--color-text-secondary)" }}>
              Land-cover anchor (DeepLabV3+, HMR validation patches, %)
            </span>
          </div>
          <table className="benchmark-table" style={{ width: "100%" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}>Class</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1</th>
                <th>IoU</th>
              </tr>
            </thead>
            <tbody>
              {LAND_COVER.map((row) => (
                <tr key={row.cls}>
                  <td style={{ fontFamily: "var(--font-sans)", fontWeight: 600, fontSize: 13 }}>{row.cls}</td>
                  <td>{row.precision.toFixed(2)}</td>
                  <td>{row.recall.toFixed(2)}</td>
                  <td>{row.f1.toFixed(2)}</td>
                  <td>{row.iou.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 6, padding: 20 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Methodology</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {PROTOCOL.items.map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 2 }}>{label}</div>
                <div style={{ fontSize: 12, color: "var(--color-text)" }}>{value}</div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
