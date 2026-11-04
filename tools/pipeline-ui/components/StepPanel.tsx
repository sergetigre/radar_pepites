"use client";

import { STAGE_COLORS, STAGE_LABELS, type StepConfig } from "@/lib/pipelineConfig";

type RunRow = {
  run_id: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  error: string | null;
};

export function StepPanel({
  step,
  isRunning,
  lastSuccess,
  recentRuns,
  log,
  onRun,
  onStop,
  onClose,
}: {
  step: StepConfig;
  isRunning: boolean;
  lastSuccess: string | null;
  recentRuns: RunRow[];
  log: string;
  onRun: () => void;
  onStop: () => void;
  onClose: () => void;
}) {
  const colors = STAGE_COLORS[step.stage];

  return (
    <div
      style={{
        width: 360,
        background: "var(--card)",
        borderLeft: "1px solid var(--border)",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: 20,
        overflowY: "auto",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <div
            style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.04em",
              textTransform: "uppercase",
              color: colors.accent,
              marginBottom: 6,
            }}
          >
            {STAGE_LABELS[step.stage]}
          </div>
          <h2 style={{ fontSize: 17, fontWeight: 700, margin: 0 }}>{step.label}</h2>
        </div>
        <button
          onClick={onClose}
          style={{
            border: "none",
            background: "transparent",
            fontSize: 18,
            color: "var(--text-faint)",
            cursor: "pointer",
            lineHeight: 1,
          }}
          aria-label="Fermer"
        >
          ×
        </button>
      </div>

      <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5, marginTop: 10 }}>
        {step.description}
      </p>

      <div style={{ fontSize: 12, color: "var(--text-faint)", marginTop: 4, marginBottom: 16 }}>
        {lastSuccess ? `Dernier succès : ${lastSuccess}` : "Jamais exécuté avec succès"}
      </div>

      <button
        onClick={isRunning ? onStop : onRun}
        style={{
          background: isRunning ? "#e0525218" : colors.accent,
          color: isRunning ? "#e05252" : "#fff",
          border: "none",
          borderRadius: 8,
          padding: "10px 14px",
          fontSize: 13,
          fontWeight: 650,
          cursor: "pointer",
          marginBottom: 16,
        }}
      >
        {isRunning ? "⏹ Arrêter" : `▶ Lancer ${step.label}`}
      </button>

      {log && (
        <pre
          style={{
            background: "#0f1115",
            color: "#d7dae0",
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            lineHeight: 1.5,
            padding: 12,
            borderRadius: 8,
            maxHeight: 260,
            overflow: "auto",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            marginBottom: 16,
          }}
        >
          {log}
        </pre>
      )}

      <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-faint)", marginBottom: 8 }}>
        Derniers runs
      </div>
      {recentRuns.length === 0 ? (
        <p style={{ fontSize: 12, color: "var(--text-faint)" }}>Aucun run enregistré.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {recentRuns.map((r) => (
            <div
              key={r.run_id}
              style={{
                fontSize: 12,
                display: "flex",
                justifyContent: "space-between",
                padding: "6px 8px",
                background: "var(--bg)",
                borderRadius: 6,
              }}
            >
              <span style={{ color: "var(--text-muted)" }}>
                {new Date(r.started_at).toLocaleString("fr-FR")}
              </span>
              <span
                style={{
                  color:
                    r.status === "success"
                      ? "#2dad7e"
                      : r.status === "failed"
                        ? "#e05252"
                        : r.status === "stopped"
                          ? "#9aa0ab"
                          : "#e0b452",
                  fontWeight: 650,
                }}
              >
                {r.status === "success"
                  ? "✓ succès"
                  : r.status === "failed"
                    ? "✗ échec"
                    : r.status === "stopped"
                      ? "⏹ arrêté"
                      : "… en cours"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
