"use client";

import { Handle, Position } from "reactflow";
import { STAGE_COLORS, type StepConfig } from "@/lib/pipelineConfig";

export type NodeStatus = "idle" | "running" | "success" | "failed" | "stopped";

export type StepNodeData = {
  step: StepConfig;
  status: NodeStatus;
  lastSuccess: string | null;
  selected: boolean;
  onClick: () => void;
  onRun: () => void;
  onStop: () => void;
};

const STATUS_DOT: Record<NodeStatus, string> = {
  idle: "#c3c7cf",
  running: "#e0b452",
  success: "#2dad7e",
  failed: "#e05252",
  stopped: "#9aa0ab",
};

const STATUS_LABEL: Record<NodeStatus, string> = {
  idle: "Jamais exécuté",
  running: "En cours...",
  success: "Succès",
  failed: "Échec",
  stopped: "Arrêté",
};

export function StepNode({ data }: { data: StepNodeData }) {
  const { step, status, lastSuccess, selected, onClick, onRun, onStop } = data;
  const colors = STAGE_COLORS[step.stage];
  const isRunning = status === "running";

  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      style={{
        background: "var(--card)",
        border: `1.5px solid ${selected ? colors.accent : "var(--border)"}`,
        borderRadius: 12,
        padding: "10px 14px",
        minWidth: 190,
        boxShadow: selected
          ? `0 0 0 3px ${colors.accent}22, 0 4px 14px rgba(0,0,0,.06)`
          : "0 1px 3px rgba(0,0,0,.04)",
        cursor: "pointer",
        transition: "box-shadow .15s, border-color .15s",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0.35 }} />
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: 999,
            background: STATUS_DOT[status],
            flexShrink: 0,
            boxShadow: isRunning ? `0 0 0 3px ${STATUS_DOT.running}33` : undefined,
          }}
        />
        <span style={{ fontSize: 13, fontWeight: 650, color: "var(--text)", flex: 1 }}>{step.label}</span>

        {isRunning ? (
          <button
            title="Arrêter"
            onClick={(e) => {
              e.stopPropagation();
              onStop();
            }}
            style={{
              width: 22,
              height: 22,
              borderRadius: 6,
              border: "none",
              background: "#e0525218",
              color: "#e05252",
              fontSize: 10,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            ⏹
          </button>
        ) : (
          <button
            title={`Lancer ${step.label}`}
            onClick={(e) => {
              e.stopPropagation();
              onRun();
            }}
            style={{
              width: 22,
              height: 22,
              borderRadius: 6,
              border: "none",
              background: colors.bg,
              color: colors.accent,
              fontSize: 10,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            ▶
          </button>
        )}
      </div>
      <div style={{ fontSize: 11, color: "var(--text-faint)", marginLeft: 16 }}>
        {isRunning
          ? STATUS_LABEL.running
          : lastSuccess
            ? `Dernier succès : ${lastSuccess}`
            : STATUS_LABEL[status]}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0.35 }} />
    </div>
  );
}
