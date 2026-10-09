"use client";

import ReactECharts from "echarts-for-react";
import type { ClassementRow } from "@/lib/queries/joueurs";
import { formatNumber } from "@/lib/format";
import { ligueColor } from "@/lib/ligue-colors";
import { teamLogoUrl } from "@/lib/media";
import { useTheme } from "@/components/theme/ThemeProvider";
import { CHART_COLORS } from "@/lib/theme/chartColors";

// Portage de web/utils/charts.py::scatter_xg_buts() — xG vs Buts, un point
// par joueur, taille par score_corrige, diagonale de référence y=x. Écart
// vs. l'original : marqueur = logo du club (demande explicite) plutôt
// qu'une bulle pleine ; fallback en cercle plein si le logo est
// indisponible (pas de team_id_ss). Couleur par ligue (legend, toggle au
// clic) = palette dédiée (lib/ligue-colors.ts), même logique qu'ailleurs
// sur le site — pas les vraies couleurs de marque (dim_ligues.couleur_hex),
// trop proches les unes des autres pour de la dataviz.
type Row = Pick<
  ClassementRow,
  | "joueur"
  | "equipe"
  | "age"
  | "ligue"
  | "ligue_id"
  | "score_corrige"
  | "xg_p90"
  | "buts_p90"
  | "team_id_ss"
>;

type Point = {
  value: [number, number];
  joueur: string;
  equipe: string;
  age: number;
  score_corrige: number | null;
  team_id_ss: number | null;
};

export function ScatterXgButs({ data }: { data: Row[] }) {
  const { theme } = useTheme();
  const c = CHART_COLORS[theme];
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
  const minPx = 16;
  const maxPx = 32;
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
          team_id_ss: r.team_id_ss,
        })
      ),
    symbol: (_val: number[], params: { data: Point }) => {
      const url = teamLogoUrl(params.data.team_id_ss);
      return url ? `image://${url}` : "circle";
    },
    symbolSize: (_val: number[], params: { data: Point }) => sizeFor(params.data.score_corrige ?? 0),
    label: {
      show: true,
      position: "top",
      distance: 4,
      fontSize: 9,
      color: c.textMuted,
      formatter: (params: { data: Point }) => params.data.joueur,
    },
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
    lineStyle: { color: c.grid, type: "dashed", width: 1 },
    tooltip: { show: false },
    z: 1,
  };

  const option = {
    backgroundColor: "transparent",
    grid: { left: 60, right: 20, top: 70, bottom: 55 },
    legend: {
      data: ligueOrder,
      top: 0,
      icon: "circle",
      itemGap: 14,
      itemWidth: 10,
      itemHeight: 10,
      padding: [0, 0, 12, 0],
      textStyle: { color: c.text },
    },
    xAxis: {
      type: "value",
      name: "xG / 90 min",
      nameLocation: "middle",
      nameGap: 28,
      nameTextStyle: { color: c.textMuted },
      min: 0,
      max: maxAxis,
      splitLine: { lineStyle: { color: c.grid } },
      axisLabel: { color: c.textMuted, formatter: (v: number) => v.toFixed(2) },
    },
    yAxis: {
      type: "value",
      name: "Buts / 90 min",
      nameLocation: "middle",
      nameGap: 40,
      nameTextStyle: { color: c.textMuted },
      min: 0,
      max: maxAxis,
      splitLine: { lineStyle: { color: c.grid } },
      axisLabel: { color: c.textMuted, formatter: (v: number) => v.toFixed(2) },
    },
    series: [...series, refLine],
    tooltip: {
      trigger: "item",
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.text },
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
