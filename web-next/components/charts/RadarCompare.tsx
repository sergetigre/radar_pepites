"use client";

import ReactECharts from "echarts-for-react";
import { RADAR_LABELS } from "@/lib/charts-config";
import { formatNumber } from "@/lib/format";

// Portage de web/utils/charts.py::radar_compare() — deux traces (A vert,
// B rouge), pas de trace "Moyenne" (contrairement à radar_single).
export function RadarCompare({
  rowA,
  rowB,
  axes,
  nameA,
  nameB,
}: {
  rowA: Record<string, unknown>;
  rowB: Record<string, unknown>;
  axes: string[];
  nameA: string;
  nameB: string;
}) {
  const labels = axes.map((a) => RADAR_LABELS[a] ?? a);
  const valsA = axes.map((a) => Number(rowA[a] ?? 0));
  const valsB = axes.map((a) => Number(rowB[a] ?? 0));

  const option = {
    backgroundColor: "transparent",
    legend: {
      data: [nameA, nameB],
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
            name: nameA,
            value: valsA,
            lineStyle: { color: "#2DAD7E", width: 2 },
            areaStyle: { color: "rgba(45,173,126,0.2)" },
            itemStyle: { color: "#2DAD7E" },
          },
          {
            name: nameB,
            value: valsB,
            lineStyle: { color: "#E05252", width: 2 },
            areaStyle: { color: "rgba(224,84,82,0.2)" },
            itemStyle: { color: "#E05252" },
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

  return <ReactECharts option={option} style={{ height: 480, width: "100%" }} notMerge />;
}
