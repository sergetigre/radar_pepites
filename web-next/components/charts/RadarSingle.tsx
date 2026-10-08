"use client";

import ReactECharts from "echarts-for-react";
import { RADAR_AXES, RADAR_LABELS } from "@/lib/charts-config";
import { formatNumber } from "@/lib/format";

// Portage de web/utils/charts.py::radar_single() — trace "Moyenne" en
// pointillés à 50 partout (référence), trace joueur par-dessus.
export function RadarSingle({
  row,
  poste,
  name,
  color,
}: {
  row: Record<string, unknown>;
  poste: string;
  name: string;
  color: string;
}) {
  const axes = RADAR_AXES[poste] ?? RADAR_AXES["CM"];
  const vals = axes.map((a) => Number(row[a] ?? 0));
  const labels = axes.map((a) => RADAR_LABELS[a] ?? a);

  const hex = color.replace("#", "");
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);

  const option = {
    backgroundColor: "transparent",
    legend: {
      data: ["Moyenne", name],
      bottom: 0,
      textStyle: { color: "#FFFFFF" },
    },
    radar: {
      indicator: labels.map((l) => ({ name: l, max: 100 })),
      shape: "polygon",
      splitNumber: 4,
      axisName: { color: "#FFFFFF", fontSize: 9 },
      splitLine: { lineStyle: { color: "#1A1A1A" } },
      splitArea: { areaStyle: { color: ["#111111", "#111111"] } },
      axisLine: { lineStyle: { color: "#1A1A1A" } },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            name: "Moyenne",
            value: axes.map(() => 50),
            symbol: "none",
            lineStyle: { color: "rgba(255,255,255,0.15)", type: "dashed", width: 1 },
            areaStyle: { color: "rgba(255,255,255,0.02)" },
            itemStyle: { color: "rgba(255,255,255,0.15)" },
          },
          {
            name,
            value: vals,
            lineStyle: { color, width: 2 },
            areaStyle: { color: `rgba(${r},${g},${b},0.2)` },
            itemStyle: { color },
          },
        ],
      },
    ],
    tooltip: {
      trigger: "item",
      backgroundColor: "#111111",
      borderColor: "#1A1A1A",
      textStyle: { color: "#FFFFFF" },
      formatter: (params: { seriesName: string; value: number[] }) => {
        const lines = labels.map((l, i) => `${l} : ${formatNumber(params.value[i])}`).join("<br/>");
        return `<b>${params.seriesName}</b><br/>${lines}`;
      },
    },
  };

  return <ReactECharts option={option} style={{ height: 420, width: "100%" }} notMerge />;
}
