import { query } from "@/lib/db";

export type GkFiche = {
  stat_id: number;
  joueur_id: number;
  ligue_id: string;
  saison_id: string;
  est_u23: boolean;
  age: number;
  minutes: number;
  matchs_joues: number;
  saves_p90: number | null;
  goals_prevented: number | null;
  save_pct: number | null;
  clean_sheets_pct: number | null;
  long_balls_pct: number | null;
  rating: number | null;
  pct_saves_p90: number | null;
  pct_goals_prevented: number | null;
  pct_save_pct: number | null;
  pct_clean_sheets_pct: number | null;
  pct_long_balls_pct: number | null;
  score_pepite: number | null;
  score_pepite_corrige: number | null;
  score_rang_ligue: number | null;
  score_rang_global: number | null;
  has_fbref_data: boolean;
  has_sofascore_data: boolean;
  nom_complet: string;
  nom_court: string | null;
  date_naissance: string | null;
  nationalite_principale: string | null;
  pied_dominant: string | null;
  taille_cm: number | null;
  player_id_ss: number | null;
  equipe: string;
  team_id_ss: number | null;
  ligue: string;
  ligue_court: string;
  couleur_hex: string | null;
  saison_courte: string;
};

// Portage 1:1 de web/utils/db.py::get_gk_fiche() — sourcée de fact_stats
// (pas keepers_combined) pour disposer des percentiles et du score_pepite.
export async function getGkFiche(joueurId: number, saison: string): Promise<GkFiche | null> {
  const rows = await query`
    SELECT
      f.stat_id, f.joueur_id, f.ligue_id, f.saison_id,
      f.est_u23, f.age,
      f.minutes, f.matchs_joues,
      f.saves_p90, f.goals_prevented, f.save_pct, f.clean_sheets_pct,
      f.long_balls_pct, f.rating,
      f.pct_saves_p90, f.pct_goals_prevented, f.pct_save_pct,
      f.pct_clean_sheets_pct, f.pct_long_balls_pct,
      f.score_pepite, f.score_pepite_corrige,
      f.score_rang_ligue, f.score_rang_global,
      f.has_fbref_data, f.has_sofascore_data,
      j.nom_complet, j.nom_court, j.date_naissance,
      j.nationalite_principale, j.pied_dominant, j.taille_cm, j.player_id_ss,
      e.nom_complet as equipe, e.team_id_ss,
      l.nom_complet as ligue, l.nom_court as ligue_court, l.couleur_hex,
      s.saison_courte
    FROM public.fact_stats f
    JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
    JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
    JOIN public.dim_ligues  l ON f.ligue_id  = l.ligue_id
    JOIN public.dim_saisons s ON f.saison_id = s.saison_id
    WHERE f.joueur_id = ${joueurId} AND f.saison_id = ${saison}
      AND f.poste_id = 'GK'
    LIMIT 1
  `;
  return (rows[0] as GkFiche) ?? null;
}

export type ProgressionGkRow = {
  saison_id: string;
  saison_courte: string;
  minutes: number;
  matchs_joues: number;
  saves_p90: number | null;
  goals_prevented: number | null;
  save_pct: number | null;
  clean_sheets_pct: number | null;
  rating: number | null;
  has_fbref_data: boolean;
  score_pepite_corrige: number | null;
  nom_complet: string;
  nom_court: string | null;
};

// Portage de web/utils/db.py::get_progression_gk() — même ajout de
// j.nom_complet/nom_court que getProgressionJoueur() (cf. commentaire
// associé dans lib/queries/joueurs.ts).
export async function getProgressionGk(joueurId: number): Promise<ProgressionGkRow[]> {
  const rows = await query`
    SELECT
      f.saison_id, s.saison_courte,
      f.minutes, f.matchs_joues,
      f.saves_p90, f.goals_prevented, f.save_pct, f.clean_sheets_pct,
      f.rating, f.has_fbref_data, f.score_pepite_corrige,
      j.nom_complet, j.nom_court
    FROM public.fact_stats f
    JOIN public.dim_saisons s ON f.saison_id = s.saison_id
    JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
    WHERE f.joueur_id = ${joueurId} AND f.poste_id = 'GK'
    ORDER BY f.saison_id ASC
  `;
  return rows as ProgressionGkRow[];
}

export type ClassementGkRow = {
  player_id_ss: number;
  player_name: string;
  team_name: string;
  ligue_id: string;
  age_actuel: number;
  saves_p90: number | null;
  goals_prevented_ss: number | null;
  save_pct_fb: number | null;
  clean_sheets_fb: number | null;
  minutes_ss: number;
  team_id_ss: number | null;
};

// Portage de web/utils/db.py::get_classement_gk() — listing seulement
// (gold.vue_top_u23_gk, sourcée de silver.keepers_combined), SANS Score
// Pépite : incohérence connue avec /championnats (get_top_gk_score/
// fact_stats, avec score), tranchée explicitement avec l'utilisateur —
// ne pas corriger ici, reproduire le comportement actuel à l'identique.
// Ajout de team_id_ss (logo club) : vue_top_u23_gk n'a pas d'equipe_id
// direct, donc jointure via dim_joueurs.player_id_ss -> fact_stats (même
// joueur_id + saison_id) -> dim_equipes, sans duplication de lignes.
export async function getClassementGk(
  saison: string,
  ligues: string[],
  minMin: number
): Promise<ClassementGkRow[]> {
  if (ligues.length === 0) return [];
  const rows = await query`
    SELECT
      g.player_id_ss, g.player_name, g.team_name, g.ligue_id, g.age_actuel,
      g.saves_p90, g.goals_prevented_ss, g.save_pct_fb, g.clean_sheets_fb, g.minutes_ss,
      e.team_id_ss
    FROM gold.vue_top_u23_gk g
    LEFT JOIN public.dim_joueurs j ON j.player_id_ss = g.player_id_ss
    LEFT JOIN public.fact_stats f ON f.joueur_id = j.joueur_id AND f.saison_id = g.saison_id
    LEFT JOIN public.dim_equipes e ON e.equipe_id = f.equipe_id
    WHERE g.saison_id = ${saison} AND g.ligue_id = ANY(${ligues})
      AND g.minutes_ss >= ${minMin}
    ORDER BY g.saves_p90 DESC NULLS LAST
  `;
  return rows as ClassementGkRow[];
}

export type TopGkScoreRow = {
  joueur_id: number;
  joueur: string;
  equipe: string;
  age: number;
  score_corrige: number | null;
  ligue: string;
  ligue_id: string;
  team_id_ss: number | null;
};

// Portage de web/utils/db.py::get_top_gk_score() — sourcé directement de
// fact_stats (pas gold.vue_top_u23_gk, dont le player_id_ss n'est pas
// compatible avec joueur_id/get_gk_fiche) : donne le vrai joueur_id
// utilisable pour un lien Radar GK et le score_pepite_corrige. ligueId
// (string) devenu ligueIds (string[]) + ajout nationalites : page
// Championnats désormais multi-ligues, avec critère nationalité. Ajout
// ligue_id + team_id_ss (logos).
export async function getTopGkScore(
  saison: string,
  ligueIds: string[],
  minMin: number,
  ageMax: number,
  n: number,
  nationalites: string[]
): Promise<TopGkScoreRow[]> {
  if (ligueIds.length === 0 || nationalites.length === 0) return [];
  const rows = await query`
    SELECT f.joueur_id, j.nom_complet AS joueur, e.nom_complet AS equipe,
           f.age, f.score_pepite_corrige AS score_corrige,
           l.nom_complet AS ligue, f.ligue_id, e.team_id_ss
    FROM public.fact_stats f
    JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
    JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
    JOIN public.dim_ligues  l ON f.ligue_id  = l.ligue_id
    WHERE f.poste_id = 'GK' AND f.est_u23 = TRUE AND f.ligue_id = ANY(${ligueIds})
      AND f.saison_id = ${saison} AND f.minutes >= ${minMin}
      AND f.age <= ${ageMax} AND j.nationalite_principale = ANY(${nationalites})
    ORDER BY f.score_pepite_corrige DESC NULLS LAST
    LIMIT ${n}
  `;
  return rows as TopGkScoreRow[];
}
