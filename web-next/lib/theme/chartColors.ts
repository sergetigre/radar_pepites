import type { Theme } from "./theme";

// ECharts prend des couleurs JS brutes (pas de CSS custom properties dans
// le canvas) — contrairement au reste du site, chaque composant graphique
// doit donc choisir sa palette explicitement selon le thème courant
// (useTheme()), d'où cette table miroir des variables de globals.css.
export type ChartColors = {
  text: string;
  textMuted: string;
  grid: string;
  tooltipBg: string;
  tooltipBorder: string;
  cardBg: string;
  faint: string;
  faintArea: string;
};

export const CHART_COLORS: Record<Theme, ChartColors> = {
  dark: {
    text: "#FFFFFF",
    textMuted: "#8A8A8A",
    grid: "#1A1A1A",
    tooltipBg: "#111111",
    tooltipBorder: "#1A1A1A",
    cardBg: "#111111",
    faint: "rgba(255,255,255,0.15)",
    faintArea: "rgba(255,255,255,0.02)",
  },
  light: {
    text: "#15171A",
    textMuted: "#6B7280",
    grid: "#E3E3E5",
    tooltipBg: "#FFFFFF",
    tooltipBorder: "#E3E3E5",
    cardBg: "#F5F5F6",
    faint: "rgba(0,0,0,0.15)",
    faintArea: "rgba(0,0,0,0.03)",
  },
};
