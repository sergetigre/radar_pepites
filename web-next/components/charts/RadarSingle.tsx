"use client";

import ReactECharts from "echarts-for-react";
import { RADAR_AXES, RADAR_LABELS } from "@/lib/charts-config";
import { formatNumber } from "@/lib/format";
import { useTheme } from "@/components/theme/ThemeProvider";
import { CHART_COLORS } from "@/lib/theme/chartColors";

// Portage de web/utils/charts.py::radar_single() — trace "Moyenne" en
// pointillés à 50 partout (référence), trace joueur par-dessus.
export function RadarSingle({
  row,
  poste,
  name,
  color,
  labels: labelsOverride,
}: {
  row: Record<string, unknown>;
  poste: string;
  name: string;
  color: string;
  labels?: Record<string, string>;
}) {
  const { theme } = useTheme();
  const c = CHART_COLORS[theme];
  const axes = RADAR_AXES[poste] ?? RADAR_AXES["CM"];
  const vals = axes.map((a) => Number(row[a] ?? 0));
  const labelMap = labelsOverride ?? RADAR_LABELS;
  const labels = axes.map((a) => labelMap[a] ?? a);

  const hex = color.replace("#", "");
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);

  const option = {
    backgroundColor: "transparent",
    legend: {
      data: ["Moyenne", name],
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
            name: "Moyenne",
            value: axes.map(() => 50),
            symbol: "none",
            lineStyle: { color: c.faint, type: "dashed", width: 1 },
            areaStyle: { color: c.faintArea },
            itemStyle: { color: c.faint },
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
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.text },
      formatter: (params: { seriesName: string; value: number[] }) => {
        const lines = labels.map((l, i) => `${l} : ${formatNumber(params.value[i])}`).join("<br/>");
        return `<b>${params.seriesName}</b><br/>${lines}`;
      },
    },
  };

  return <ReactECharts option={option} style={{ height: 420, width: "100%" }} notMerge />;
}
