"use client";

import ReactECharts from "echarts-for-react";
import type { ProgressionRow } from "./LineProgression";
import { formatNumber } from "@/lib/format";

// Portage 1:1 de web/utils/charts.py::bar_progression() — labels/couleurs
// FIXES par position dans `cols`, indépendants des couleurs par-métrique de
// line_progression. Ce dict ne couvre que les 6 métriques "joueur de champ" ;
// pour les métriques GK (saves_p90, goals_prevented), `labels.get(col, col)`
// retombe sur le nom de colonne brut dans l'original — reproduit tel quel
// ici plutôt que "corrigé", pour rester fidèle au comportement réel observé
// en vue "Barres groupées" de Progression GK.
const BAR_LABELS: Record<string, string> = {
  buts_p90: "Buts/90",
  xg_p90: "xG/90",
  passes_dec_p90: "Assists/90",
  key_passes_p90: "KP/90",
  dribbles_p90: "Drib/90",
  tackles_p90: "Tac/90",
};
const BAR_COLORS = ["#2DAD7E", "#5DCBA0", "#E0B452", "#4ECDC4", "#FF6B35", "#E05252"];

export function BarProgression({
  data,
  joueur,
  cols,
}: {
  data: ProgressionRow[];
  joueur: string;
  cols: string[];
}) {
  const categories = data.map((d) => d.saison_courte);

  const series = cols.map((col, i) => ({
    name: BAR_LABELS[col] ?? col,
    type: "bar",
    data: data.map((d) => (typeof d[col] === "number" ? (d[col] as number) : null)),
    itemStyle: { color: BAR_COLORS[i % BAR_COLORS.length] },
  }));

  const option = {
    backgroundColor: "transparent",
    title: { text: joueur, left: "center", textStyle: { fontSize: 13, color: "#FFFFFF" } },
    legend: { bottom: 0, textStyle: { color: "#FFFFFF" } },
    grid: { top: 50, left: 55, right: 30, bottom: 60, backgroundColor: "#111111" },
    xAxis: {
      type: "category",
      data: categories,
      axisLabel: { color: "#8A8A8A" },
      axisLine: { lineStyle: { color: "#1A1A1A" } },
    },
    yAxis: {
      type: "value",
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

  return <ReactECharts option={option} style={{ height: 400, width: "100%" }} notMerge />;
}
