"use client";

import ReactECharts from "echarts-for-react";
import { formatNumber } from "@/lib/format";

export type ProgressionRow = { saison_courte: string } & Record<
  string,
  number | boolean | string | null
>;

export type Metric = { col: string; label: string; color: string };

// Portage de web/utils/charts.py::line_progression() — valeurs brutes par
// saison, une courbe par métrique avec sa couleur fixe.
export function LineProgression({
  data,
  joueur,
  metrics,
}: {
  data: ProgressionRow[];
  joueur: string;
  metrics: Metric[];
}) {
  const categories = data.map((d) => d.saison_courte);

  const series = metrics.map((m) => ({
    name: m.label,
    type: "line",
    data: data.map((d) => (typeof d[m.col] === "number" ? (d[m.col] as number) : null)),
    lineStyle: { color: m.color, width: 2 },
    itemStyle: { color: m.color },
    symbolSize: 8,
    label: {
      show: true,
      position: "top",
      color: m.color,
      fontSize: 9,
      formatter: (p: { value: number | null }) => (p.value != null ? formatNumber(p.value) : ""),
    },
  }));

  const option = {
    backgroundColor: "transparent",
    title: {
      text: `Progression — ${joueur}`,
      left: "center",
      textStyle: { fontSize: 13, color: "#FFFFFF" },
    },
    legend: { bottom: 0, textStyle: { color: "#FFFFFF" } },
    grid: { top: 50, left: 55, right: 30, bottom: 60, backgroundColor: "#111111" },
    xAxis: {
      type: "category",
      name: "Saison",
      nameLocation: "middle",
      nameGap: 30,
      nameTextStyle: { color: "#8A8A8A" },
      data: categories,
      axisLabel: { color: "#8A8A8A" },
      axisLine: { lineStyle: { color: "#1A1A1A" } },
    },
    yAxis: {
      type: "value",
      name: "Valeur /90 min",
      nameTextStyle: { color: "#8A8A8A" },
      axisLabel: { color: "#8A8A8A", formatter: (v: number) => formatNumber(v) },
      splitLine: { lineStyle: { color: "#1A1A1A" } },
    },
    series,
    tooltip: {
      trigger: "axis",
      backgroundColor: "#111111",
      borderColor: "#1A1A1A",
      textStyle: { color: "#FFFFFF" },
      valueFormatter: (v: number | string) => (typeof v === "number" ? formatNumber(v) : String(v)),
    },
  };

  return <ReactECharts option={option} style={{ height: 420, width: "100%" }} notMerge />;
}
