"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, { Background, Controls, type Edge, type Node } from "reactflow";
import { EDGES, STEPS, STEPS_BY_KEY, type StepKey } from "@/lib/pipelineConfig";
import { StepNode, type StepNodeData, type NodeStatus } from "@/components/StepNode";
import { StepPanel } from "@/components/StepPanel";

type RunRow = {
  run_id: number;
  stage: string;
  step: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  error: string | null;
};

type HistoryResponse = {
  runs: RunRow[];
  lastSuccess: { step: string; finished_at: string }[];
  runningSteps: string[];
};

const nodeTypes = { step: StepNode };

export default function PipelinePage() {
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [selected, setSelected] = useState<StepKey | null>(null);
  const [runningStep, setRunningStep] = useState<StepKey | null>(null);
  const [log, setLog] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchHistory = useCallback(async () => {
    const res = await fetch("/api/history");
    if (res.ok) setHistory(await res.json());
  }, []);

  useEffect(() => {
    fetchHistory();
    pollRef.current = setInterval(fetchHistory, 5000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchHistory]);

  const lastSuccessByStep = useMemo(() => {
    const map: Record<string, string> = {};
    for (const row of history?.lastSuccess ?? []) {
      map[row.step] = new Date(row.finished_at).toLocaleString("fr-FR");
    }
    return map;
  }, [history]);

  function statusFor(key: StepKey): NodeStatus {
    if (runningStep === key) return "running";
    const last = history?.runs.find((r) => r.step === key);
    if (!last) return "idle";
    if (last.status === "running") return "running";
    if (last.status === "success") return "success";
    if (last.status === "stopped") return "stopped";
    return "failed";
  }

  async function runStep(key: StepKey) {
    setRunningStep(key);
    setLog("");
    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: key, action: "run" }),
      });
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (reader) {
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          setLog((prev) => (prev + chunk).slice(-8000));
          await fetchHistory();
        }
      }
    } finally {
      setRunningStep(null);
      await fetchHistory();
    }
  }

  async function stopStep(key: StepKey) {
    setLog((prev) => prev + "\n--- Arrêt demandé ---\n");
    await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ step: key, action: "stop" }),
    });
    // Le fetch /api/run (run) ci-dessus se termine de son côté quand le
    // process tué ferme son stdout — pas besoin de setRunningStep(null) ici.
    await fetchHistory();
  }

  const nodes: Node<StepNodeData>[] = STEPS.map((step) => ({
    id: step.key,
    type: "step",
    position: step.position,
    data: {
      step,
      status: statusFor(step.key),
      lastSuccess: lastSuccessByStep[step.key] ?? null,
      selected: selected === step.key,
      onClick: () => setSelected(step.key),
      onRun: () => runStep(step.key),
      onStop: () => stopStep(step.key),
    },
    draggable: false,
  }));

  const edges: Edge[] = EDGES.map((e) => ({
    id: `${e.source}-${e.target}`,
    source: e.source,
    target: e.target,
    animated: runningStep === e.source,
    style: { stroke: "#c3c7cf", strokeWidth: 1.5 },
  }));

  const selectedStep = selected ? STEPS_BY_KEY[selected] : null;
  const recentRunsForSelected = (history?.runs ?? []).filter((r) => r.step === selected).slice(0, 8);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          height: 56,
          background: "var(--card)",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          padding: "0 20px",
          gap: 10,
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 15, fontWeight: 700 }}>RadarPépites</span>
        <span style={{ color: "var(--text-faint)", fontSize: 13 }}>/ Pipeline</span>
        <span
          style={{
            marginLeft: "auto",
            fontSize: 11,
            color: "var(--text-faint)",
            fontFamily: "var(--font-mono)",
          }}
        >
          outil local — jamais déployé
        </span>
      </header>

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        <div style={{ flex: 1, position: "relative" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            proOptions={{ hideAttribution: true }}
            nodesConnectable={false}
            elementsSelectable={false}
            onPaneClick={() => setSelected(null)}
          >
            <Background color="#d8dbe2" gap={20} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>

        {selectedStep && (
          <StepPanel
            step={selectedStep}
            isRunning={runningStep === selectedStep.key}
            lastSuccess={lastSuccessByStep[selectedStep.key] ?? null}
            recentRuns={recentRunsForSelected}
            log={runningStep === selectedStep.key ? log : ""}
            onRun={() => runStep(selectedStep.key)}
            onStop={() => stopStep(selectedStep.key)}
            onClose={() => setSelected(null)}
          />
        )}
      </div>
    </div>
  );
}
