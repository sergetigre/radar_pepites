"use client";

import ReactECharts from "echarts-for-react";
import type { ClassementRow } from "@/lib/queries/joueurs";
import { formatNumber } from "@/lib/format";

// Portage de web/utils/charts.py::bar_top10() — barres horizontales,
// colorscale continue verte, étiquette de score en bout de barre.
export function BarTop10({ data }: { data: Pick<ClassementRow, "joueur" | "score_corrige">[] }) {
  const top10 = data.slice(0, 10);
  const scores = top10.map((d) => d.score_corrige ?? 0);
  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);

  const option = {
    backgroundColor: "transparent",
    grid: { left: 150, right: 55, top: 10, bottom: 10, backgroundColor: "#111111" },
    xAxis: {
      type: "value",
      min: 0,
      max: 105,
      splitLine: { lineStyle: { color: "#1A1A1A" } },
      axisLabel: { color: "#8A8A8A" },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: top10.map((d) => d.joueur),
      axisLabel: { color: "#FFFFFF" },
      axisLine: { lineStyle: { color: "#1A1A1A" } },
      axisTick: { show: false },
    },
    visualMap: {
      show: false,
      min: minScore,
      max: maxScore,
      dimension: 0,
      inRange: { color: ["#0F5436", "#2DAD7E", "#5DCBA0"] },
    },
    series: [
      {
        type: "bar",
        data: scores,
        barWidth: "60%",
        label: {
          show: true,
          position: "right",
          color: "#FFFFFF",
          formatter: (p: { value: number }) => formatNumber(p.value),
        },
      },
    ],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "none" },
      backgroundColor: "#111111",
      borderColor: "#1A1A1A",
      textStyle: { color: "#FFFFFF" },
      formatter: (params: { name: string; value: number }[]) =>
        `<b>${params[0].name}</b><br/>Score : ${formatNumber(params[0].value)}`,
    },
  };

  return <ReactECharts option={option} style={{ height: 380, width: "100%" }} notMerge />;
}
