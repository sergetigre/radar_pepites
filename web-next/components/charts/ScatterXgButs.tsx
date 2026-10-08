"use client";

import ReactECharts from "echarts-for-react";
import type { ClassementRow } from "@/lib/queries/joueurs";
import { formatNumber } from "@/lib/format";
import { ligueColor } from "@/lib/ligue-colors";

// Portage de web/utils/charts.py::scatter_xg_buts() — bulles xG vs Buts,
// couleur par ligue, taille par score_corrige, diagonale de référence y=x.
// Couleur par ligue = palette dédiée (lib/ligue-colors.ts), la même que
// partout ailleurs sur le site (cartes joueurs, header) — pas les vraies
// couleurs de marque (dim_ligues.couleur_hex), trop proches les unes des
// autres pour de la dataviz (plusieurs rouges, Pro League en noir invisible
// sur fond sombre).
type Row = Pick<
  ClassementRow,
  "joueur" | "equipe" | "age" | "ligue" | "ligue_id" | "score_corrige" | "xg_p90" | "buts_p90"
>;

type Point = {
  value: [number, number];
  joueur: string;
  equipe: string;
  age: number;
  score_corrige: number | null;
};

export function ScatterXgButs({ data }: { data: Row[] }) {
  const rows = data.filter((d) => d.xg_p90 != null && d.buts_p90 != null);

  const ligueOrder: string[] = [];
  const ligueColors = new Map<string, string>();
  for (const r of rows) {
    if (!ligueOrder.includes(r.ligue)) {
      ligueOrder.push(r.ligue);
      ligueColors.set(r.ligue, ligueColor(r.ligue_id));
    }
  }

  const scores = rows.map((r) => r.score_corrige ?? 0);
  const minScore = Math.min(...scores, 0);
  const maxScore = Math.max(...scores, 1);
  const minPx = 4;
  const maxPx = 15;
  const sizeFor = (score: number) => {
    if (maxScore === minScore) return (minPx + maxPx) / 2;
    const t = Math.sqrt((score - minScore) / (maxScore - minScore));
    return minPx + t * (maxPx - minPx);
  };

  const maxAxis = rows.length
    ? Math.max(...rows.map((r) => Math.max(r.xg_p90 ?? 0, r.buts_p90 ?? 0))) * 1.1
    : 1;

  const series = ligueOrder.map((ligue) => ({
    name: ligue,
    type: "scatter",
    color: ligueColors.get(ligue),
    data: rows
      .filter((r) => r.ligue === ligue)
      .map(
        (r): Point => ({
          value: [r.xg_p90 as number, r.buts_p90 as number],
          joueur: r.joueur,
          equipe: r.equipe,
          age: r.age,
          score_corrige: r.score_corrige,
        })
      ),
    symbolSize: (_val: number[], params: { data: Point }) => sizeFor(params.data.score_corrige ?? 0),
  }));

  const refLine = {
    name: "",
    type: "line",
    data: [
      [0, 0],
      [maxAxis, maxAxis],
    ],
    showSymbol: false,
    silent: true,
    lineStyle: { color: "rgba(255,255,255,0.2)", type: "dashed", width: 1 },
    tooltip: { show: false },
    z: 1,
  };

  const option = {
    backgroundColor: "transparent",
    grid: { left: 60, right: 20, top: 70, bottom: 55, backgroundColor: "#111111" },
    legend: {
      data: ligueOrder,
      top: 0,
      icon: "circle",
      itemGap: 14,
      itemWidth: 10,
      itemHeight: 10,
      padding: [0, 0, 12, 0],
      textStyle: { color: "#DADADA" },
    },
    xAxis: {
      type: "value",
      name: "xG / 90 min",
      nameLocation: "middle",
      nameGap: 28,
      nameTextStyle: { color: "#8A8A8A" },
      min: 0,
      max: maxAxis,
      splitLine: { lineStyle: { color: "#1A1A1A" } },
      axisLabel: { color: "#8A8A8A", formatter: (v: number) => v.toFixed(2) },
    },
    yAxis: {
      type: "value",
      name: "Buts / 90 min",
      nameLocation: "middle",
      nameGap: 40,
      nameTextStyle: { color: "#8A8A8A" },
      min: 0,
      max: maxAxis,
      splitLine: { lineStyle: { color: "#1A1A1A" } },
      axisLabel: { color: "#8A8A8A", formatter: (v: number) => v.toFixed(2) },
    },
    series: [...series, refLine],
    tooltip: {
      trigger: "item",
      backgroundColor: "#111111",
      borderColor: "#1A1A1A",
      textStyle: { color: "#FFFFFF" },
      formatter: (p: { data?: Point; value: [number, number] }) => {
        if (!p.data?.joueur) return "";
        const [xg, buts] = p.value;
        return `<b>${p.data.joueur}</b><br/>${p.data.equipe} · ${p.data.age} ans<br/>Score : ${formatNumber(
          p.data.score_corrige
        )}<br/>xG/90 : ${formatNumber(xg)}<br/>Buts/90 : ${formatNumber(buts)}`;
      },
    },
  };

  return <ReactECharts option={option} style={{ height: 400, width: "100%" }} notMerge />;
}
