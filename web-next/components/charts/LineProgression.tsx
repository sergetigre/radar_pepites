"use client";

import ReactECharts from "echarts-for-react";
import { formatNumber } from "@/lib/format";
import { useTheme } from "@/components/theme/ThemeProvider";
import { CHART_COLORS } from "@/lib/theme/chartColors";
import { useI18n } from "@/components/i18n/I18nProvider";

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
  const { theme } = useTheme();
  const { t } = useI18n();
  const c = CHART_COLORS[theme];
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
      text: `${t.progression.title} — ${joueur}`,
      left: "center",
      textStyle: { fontSize: 13, color: c.text },
    },
    legend: { bottom: 0, textStyle: { color: c.text } },
    grid: { top: 50, left: 55, right: 30, bottom: 60 },
    xAxis: {
      type: "category",
      name: t.progression.axisSeason,
      nameLocation: "middle",
      nameGap: 30,
      nameTextStyle: { color: c.textMuted },
      data: categories,
      axisLabel: { color: c.textMuted },
      axisLine: { lineStyle: { color: c.grid } },
    },
    yAxis: {
      type: "value",
      name: t.progression.axisValue,
      nameTextStyle: { color: c.textMuted },
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

  return <ReactECharts option={option} style={{ height: 420, width: "100%" }} notMerge />;
}
