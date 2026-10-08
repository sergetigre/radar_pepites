// Portage 1:1 de web/utils/charts.py::RADAR_AXES / RADAR_LABELS.

export const RADAR_AXES: Record<string, string[]> = {
  GK: ["pct_saves_p90", "pct_goals_prevented", "pct_save_pct", "pct_clean_sheets_pct", "pct_long_balls_pct"],
  CB: ["pct_interceptions_p90", "pct_tackles_p90", "pct_degagements_p90", "pct_duels_aeriens_pct", "pct_passes_pct"],
  LB: ["pct_key_passes_p90", "pct_tackles_p90", "pct_dribbles_p90", "pct_passes_pct", "pct_interceptions_p90", "pct_assists_p90"],
  RB: ["pct_key_passes_p90", "pct_tackles_p90", "pct_dribbles_p90", "pct_passes_pct", "pct_interceptions_p90", "pct_assists_p90"],
  DM: ["pct_tackles_p90", "pct_interceptions_p90", "pct_passes_pct", "pct_key_passes_p90", "pct_degagements_p90"],
  CM: ["pct_passes_pct", "pct_key_passes_p90", "pct_tackles_p90", "pct_interceptions_p90", "pct_xg_p90", "pct_assists_p90"],
  AM: ["pct_xg_p90", "pct_xag_p90", "pct_key_passes_p90", "pct_assists_p90", "pct_dribbles_p90", "pct_goals_p90"],
  LW: ["pct_goals_p90", "pct_xg_p90", "pct_dribbles_p90", "pct_key_passes_p90", "pct_assists_p90", "pct_shots_p90"],
  RW: ["pct_goals_p90", "pct_xg_p90", "pct_dribbles_p90", "pct_key_passes_p90", "pct_assists_p90", "pct_shots_p90"],
  FW: ["pct_goals_p90", "pct_xg_p90", "pct_shots_p90", "pct_duels_aeriens_pct", "pct_assists_p90", "pct_dribbles_p90"],
  MF: ["pct_passes_pct", "pct_key_passes_p90", "pct_tackles_p90", "pct_interceptions_p90", "pct_xg_p90", "pct_assists_p90"],
  DF: ["pct_interceptions_p90", "pct_tackles_p90", "pct_degagements_p90", "pct_duels_aeriens_pct", "pct_passes_pct"],
};

// Portage 1:1 de web/pages/03_Comparaison.py::ALL_STATS_COMPARE — liste des
// stats proposées au sélecteur (4 à 8) pour le radar de comparaison libre.
export const ALL_STATS_COMPARE: Record<string, string[]> = {
  "⚽ Offensif": ["pct_goals_p90", "pct_xg_p90", "pct_assists_p90", "pct_xag_p90", "pct_shots_p90"],
  "🎯 Passes": ["pct_key_passes_p90", "pct_passes_pct", "pct_dribbles_p90"],
  "🛡️ Défense": ["pct_tackles_p90", "pct_interceptions_p90", "pct_degagements_p90", "pct_duels_aeriens_pct"],
};

export const RADAR_LABELS: Record<string, string> = {
  pct_goals_p90: "Buts/90",
  pct_xg_p90: "xG/90",
  pct_assists_p90: "Assists/90",
  pct_xag_p90: "xAG/90",
  pct_shots_p90: "Tirs/90",
  pct_tirs_cadres_p90: "Tirs cadrés",
  pct_key_passes_p90: "Key Passes/90",
  pct_dribbles_p90: "Dribbles/90",
  pct_tackles_p90: "Tacles/90",
  pct_interceptions_p90: "Interceptions/90",
  pct_degagements_p90: "Dégagements/90",
  pct_duels_aeriens_pct: "Duels aériens",
  pct_passes_pct: "Précision passes",
  pct_saves_p90: "Arrêts/90",
  pct_goals_prevented: "Buts évités",
  pct_save_pct: "% Arrêts",
  pct_clean_sheets_pct: "Clean sheets",
  pct_long_balls_pct: "Passes longues",
};
