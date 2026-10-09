"use client";

import ReactECharts from "echarts-for-react";
import type { Metric, ProgressionRow } from "./LineProgression";
import { formatNumber } from "@/lib/format";
import { useTheme } from "@/components/theme/ThemeProvider";
import { CHART_COLORS } from "@/lib/theme/chartColors";

const BAR_COLORS = ["#2DAD7E", "#5DCBA0", "#E0B452", "#4ECDC4", "#FF6B35", "#E05252"];

export function BarProgression({
  data,
  joueur,
  metrics,
}: {
  data: ProgressionRow[];
  joueur: string;
  metrics: Metric[];
}) {
  const { theme } = useTheme();
  const c = CHART_COLORS[theme];
  const categories = data.map((d) => d.saison_courte);

  const series = metrics.map((m, i) => ({
    name: m.label,
    type: "bar",
    data: data.map((d) => (typeof d[m.col] === "number" ? (d[m.col] as number) : null)),
    itemStyle: { color: m.color ?? BAR_COLORS[i % BAR_COLORS.length] },
  }));

  const option = {
    backgroundColor: "transparent",
    title: { text: joueur, left: "center", textStyle: { fontSize: 13, color: c.text } },
    legend: { bottom: 0, textStyle: { color: c.text } },
    grid: { top: 50, left: 55, right: 30, bottom: 60 },
    xAxis: {
      type: "category",
      data: categories,
      axisLabel: { color: c.textMuted },
      axisLine: { lineStyle: { color: c.grid } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: c.textMuted, formatter: (v: number) => formatNumber(v) },
      splitLine: { lineStyle: { color: c.grid } },
    },
    series,
    tooltip: {
      trigger: "axis",
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.text },
      valueFormatter: (v: number | string) => (typeof v === "number" ? formatNumber(v) : String(v)),
    },
  };

  return <ReactECharts option={option} style={{ height: 400, width: "100%" }} notMerge />;
}
