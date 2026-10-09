"use client";

import ReactECharts from "echarts-for-react";
import { RADAR_LABELS } from "@/lib/charts-config";
import { formatNumber } from "@/lib/format";
import { useTheme } from "@/components/theme/ThemeProvider";
import { CHART_COLORS } from "@/lib/theme/chartColors";

// Portage de web/utils/charts.py::radar_compare() — deux traces (A vert,
// B rouge), pas de trace "Moyenne" (contrairement à radar_single).
export function RadarCompare({
  rowA,
  rowB,
  axes,
  nameA,
  nameB,
  labels: labelsOverride,
}: {
  rowA: Record<string, unknown>;
  rowB: Record<string, unknown>;
  axes: string[];
  nameA: string;
  nameB: string;
  labels?: Record<string, string>;
}) {
  const { theme } = useTheme();
  const c = CHART_COLORS[theme];
  const labelMap = labelsOverride ?? RADAR_LABELS;
  const labels = axes.map((a) => labelMap[a] ?? a);
  const valsA = axes.map((a) => Number(rowA[a] ?? 0));
  const valsB = axes.map((a) => Number(rowB[a] ?? 0));

  const option = {
    backgroundColor: "transparent",
    legend: {
      data: [nameA, nameB],
      bottom: 0,
      textStyle: { color: c.text },
    },
    radar: {
      indicator: labels.map((l) => ({ name: l, max: 100 })),
      shape: "polygon",
      splitNumber: 4,
      axisName: { color: c.text, fontSize: 9 },
      splitLine: { lineStyle: { color: c.grid } },
      splitArea: { areaStyle: { color: [c.cardBg, c.cardBg] } },
      axisLine: { lineStyle: { color: c.grid } },
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
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.text },
      formatter: (params: { seriesName: string; value: number[] }) => {
        const lines = labels.map((l, i) => `${l} : ${formatNumber(params.value[i])}`).join("<br/>");
        return `<b>${params.seriesName}</b><br/>${lines}`;
      },
    },
  };

  return <ReactECharts option={option} style={{ height: 480, width: "100%" }} notMerge />;
}
