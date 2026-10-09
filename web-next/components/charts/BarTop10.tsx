"use client";

import ReactECharts from "echarts-for-react";
import type { ClassementRow } from "@/lib/queries/joueurs";
import { formatNumber } from "@/lib/format";
import { useTheme } from "@/components/theme/ThemeProvider";
import { CHART_COLORS } from "@/lib/theme/chartColors";

// Portage de web/utils/charts.py::bar_top10() — barres horizontales,
// colorscale continue verte, étiquette de score en bout de barre.
export function BarTop10({ data }: { data: Pick<ClassementRow, "joueur" | "score_corrige">[] }) {
  const { theme } = useTheme();
  const c = CHART_COLORS[theme];
  const top10 = data.slice(0, 10);
  const scores = top10.map((d) => d.score_corrige ?? 0);
  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);

  const option = {
    backgroundColor: "transparent",
    grid: { left: 150, right: 55, top: 10, bottom: 10 },
    xAxis: {
      type: "value",
      min: 0,
      max: 105,
      splitLine: { lineStyle: { color: c.grid } },
      axisLabel: { color: c.textMuted },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: top10.map((d) => d.joueur),
      axisLabel: { color: c.text },
      axisLine: { lineStyle: { color: c.grid } },
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
        barWidth: "30%",
        itemStyle: { borderRadius: 6 },
        label: {
          show: true,
          position: "right",
          color: c.text,
          formatter: (p: { value: number }) => formatNumber(p.value),
        },
      },
    ],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "none" },
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.text },
      formatter: (params: { name: string; value: number }[]) =>
        `<b>${params[0].name}</b><br/>Score : ${formatNumber(params[0].value)}`,
    },
  };

  return <ReactECharts option={option} style={{ height: 380, width: "100%" }} notMerge />;
}
