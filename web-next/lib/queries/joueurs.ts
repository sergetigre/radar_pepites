import { query } from "@/lib/db";
import { DEFAULT_AGE_MAX } from "@/lib/filters";

export type ClassementRow = {
  rang_global: number;
  rang_ligue: number;
  joueur_id: number;
  joueur: string;
  nom_court: string;
  poste_id: string;
  poste_label_fr: string;
  ligue: string;
  ligue_id: string;
  equipe: string;
  pays: string;
  age: number;
  nationalite_principale: string | null;
  score_pepite: number | null;
  score_corrige: number | null;
  buts_p90: number | null;
  xg_p90: number | null;
  assists_p90: number | null;
  xag_p90: number | null;
  key_passes_p90: number | null;
  dribbles_p90: number | null;
  tackles_p90: number | null;
  interceptions_p90: number | null;
  minutes: number;
  couleur_hex: string | null;
  rating_reference: number | null;
  has_fbref_data: boolean;
  has_sofascore_data: boolean;
  team_id_ss: number | null;
};

// Portage de web/utils/db.py::get_classement() — ajout de team_id_ss (logo
// club) absent de gold.vue_score_pepite_ranking, récupéré via fact_stats/
// dim_equipes (même (joueur_id, saison_id), donc pas de duplication de
// lignes malgré le LEFT JOIN).
export async function getClassement(
  saison: string,
  ligues: string[],
  postes: string[],
  ageMax: number,
  minMin: number
): Promise<ClassementRow[]> {
  if (ligues.length === 0 || postes.length === 0) return [];
  const rows = await query`
    SELECT
      r.rang_global, r.rang_ligue, r.joueur_id,
      r.joueur, r.nom_court, r.poste_id, r.poste_label_fr,
      r.ligue, r.ligue_id, r.equipe, r.pays,
      r.age, r.nationalite_principale,
      r.score_pepite, r.score_corrige,
      r.buts_p90, r.xg_p90, r.assists_p90, r.xag_p90,
      r.key_passes_p90, r.dribbles_p90,
      r.tackles_p90, r.interceptions_p90,
      r.minutes, r.couleur_hex, r.rating_reference,
      r.has_fbref_data, r.has_sofascore_data,
      e.team_id_ss
    FROM gold.vue_score_pepite_ranking r
    LEFT JOIN public.fact_stats f ON f.joueur_id = r.joueur_id AND f.saison_id = r.saison_id
    LEFT JOIN public.dim_equipes e ON e.equipe_id = f.equipe_id
    WHERE r.est_u23 = TRUE
      AND r.saison_id = ${saison}
      AND r.minutes   >= ${minMin}
      AND r.age       <= ${ageMax}
      AND r.ligue_id  = ANY(${ligues})
      AND r.poste_id  = ANY(${postes})
    ORDER BY r.score_corrige DESC NULLS LAST
  `;
  return rows as ClassementRow[];
}

export type JoueurFiche = {
  stat_id: number;
  joueur_id: number;
  ligue_id: string;
  saison_id: string;
  poste_id: string;
  est_u23: boolean;
  age: number;
  minutes: number;
  matchs_joues: number;
  matchs_titulaire: number;
  buts: number;
  passes_dec: number;
  xg: number;
  xag: number;
  tirs: number;
  tirs_cadres: number;
  buts_p90: number | null;
  passes_dec_p90: number | null;
  xg_p90: number | null;
  xag_p90: number | null;
  tirs_p90: number | null;
  tirs_cadres_p90: number | null;
  dribbles_p90: number | null;
  key_passes_p90: number | null;
  tackles_p90: number | null;
  interceptions_p90: number | null;
  degagements_p90: number | null;
  duels_aeriens_pct: number | null;
  passes_pct: number | null;
  pct_goals_p90: number | null;
  pct_xg_p90: number | null;
  pct_assists_p90: number | null;
  pct_xag_p90: number | null;
  pct_shots_p90: number | null;
  pct_tirs_cadres_p90: number | null;
  pct_key_passes_p90: number | null;
  pct_dribbles_p90: number | null;
  pct_tackles_p90: number | null;
  pct_interceptions_p90: number | null;
  pct_degagements_p90: number | null;
  pct_duels_aeriens_pct: number | null;
  pct_passes_pct: number | null;
  score_pepite: number | null;
  score_pepite_corrige: number | null;
  score_rang_ligue: number | null;
  score_rang_global: number | null;
  rating: number | null;
  has_fbref_data: boolean;
  has_sofascore_data: boolean;
  nom_complet: string;
  nom_court: string | null;
  date_naissance: string | null;
  nationalite_principale: string | null;
  poste_principal: string | null;
  poste_detail: string | null;
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

// Portage 1:1 de web/utils/db.py::get_joueur_fiche()
export async function getJoueurFiche(joueurId: number, saison: string): Promise<JoueurFiche | null> {
  const rows = await query`
    SELECT
      f.stat_id, f.joueur_id, f.ligue_id, f.saison_id,
      f.poste_id, f.est_u23, f.age,
      f.minutes, f.matchs_joues, f.matchs_titulaire,
      f.buts, f.passes_dec, f.xg, f.xag, f.tirs, f.tirs_cadres,
      f.buts_p90, f.passes_dec_p90, f.xg_p90, f.xag_p90,
      f.tirs_p90, f.tirs_cadres_p90,
      f.dribbles_p90, f.key_passes_p90,
      f.tackles_p90, f.interceptions_p90,
      f.degagements_p90, f.duels_aeriens_pct, f.passes_pct,
      f.pct_goals_p90, f.pct_xg_p90,
      f.pct_assists_p90, f.pct_xag_p90,
      f.pct_shots_p90, f.pct_tirs_cadres_p90,
      f.pct_key_passes_p90, f.pct_dribbles_p90,
      f.pct_tackles_p90, f.pct_interceptions_p90,
      f.pct_degagements_p90, f.pct_duels_aeriens_pct,
      f.pct_passes_pct,
      f.score_pepite, f.score_pepite_corrige,
      f.score_rang_ligue, f.score_rang_global,
      f.rating, f.has_fbref_data, f.has_sofascore_data,
      j.nom_complet, j.nom_court, j.date_naissance,
      j.nationalite_principale, j.poste_principal, j.poste_detail,
      j.pied_dominant, j.taille_cm, j.player_id_ss,
      e.nom_complet as equipe, e.team_id_ss,
      l.nom_complet as ligue, l.nom_court as ligue_court, l.couleur_hex,
      s.saison_courte
    FROM public.fact_stats f
    JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
    JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
    JOIN public.dim_ligues  l ON f.ligue_id  = l.ligue_id
    JOIN public.dim_saisons s ON f.saison_id = s.saison_id
    WHERE f.joueur_id = ${joueurId} AND f.saison_id = ${saison}
    LIMIT 1
  `;
  return (rows[0] as JoueurFiche) ?? null;
}

const SIMILARITY_COLS = [
  "pct_goals_p90", "pct_xg_p90", "pct_assists_p90", "pct_xag_p90",
  "pct_shots_p90", "pct_key_passes_p90", "pct_dribbles_p90",
  "pct_tackles_p90", "pct_interceptions_p90", "pct_passes_pct",
] as const;

type SimilarityRow = {
  joueur_id: number;
  joueur: string;
  equipe: string;
  ligue: string;
  ligue_id: string;
  team_id_ss: number | null;
} & Record<(typeof SIMILARITY_COLS)[number], number | null>;

export type SimilarPlayer = {
  joueur_id: number;
  joueur: string;
  equipe: string;
  ligue: string;
  ligue_id: string;
  team_id_ss: number | null;
  similarite: number;
};

function cosineSim(a: number[], b: number[]): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  return denom > 0 ? dot / denom : 0;
}

// Portage de web/utils/db.py::get_profils_similaires() — écart volontaire
// vs. l'original : ajout de "f.age <= DEFAULT_AGE_MAX" absent côté
// Streamlit, qui pouvait remonter des joueurs hors U23 (ex. Lookman, Saka)
// comme "profil similaire" d'une pépite. Similarité cosinus calculée ici
// (TS) et non en SQL, comme en Python (pandas/numpy).
export async function getProfilsSimilaires(
  joueurId: number,
  saison: string,
  poste: string,
  n = 3
): Promise<SimilarPlayer[]> {
  const rows = (await query`
    SELECT
      f.joueur_id, j.nom_complet as joueur,
      e.nom_complet as equipe, l.nom_complet as ligue,
      f.ligue_id, e.team_id_ss,
      f.pct_goals_p90, f.pct_xg_p90,
      f.pct_assists_p90, f.pct_xag_p90,
      f.pct_shots_p90, f.pct_key_passes_p90,
      f.pct_dribbles_p90, f.pct_tackles_p90,
      f.pct_interceptions_p90, f.pct_passes_pct
    FROM public.fact_stats f
    JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
    JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
    JOIN public.dim_ligues  l ON f.ligue_id  = l.ligue_id
    WHERE f.saison_id = ${saison} AND f.poste_id = ${poste}
      AND f.minutes >= 450 AND f.score_pepite IS NOT NULL
      AND (f.age <= ${DEFAULT_AGE_MAX} OR f.joueur_id = ${joueurId})
  `) as SimilarityRow[];

  const target = rows.find((r) => r.joueur_id === joueurId);
  if (!target) return [];

  const vec = (r: SimilarityRow) => SIMILARITY_COLS.map((c) => r[c] ?? 50);
  const targetVec = vec(target);

  return rows
    .filter((r) => r.joueur_id !== joueurId)
    .map((r) => ({
      joueur_id: r.joueur_id,
      joueur: r.joueur,
      equipe: r.equipe,
      ligue: r.ligue,
      ligue_id: r.ligue_id,
      team_id_ss: r.team_id_ss,
      similarite: cosineSim(targetVec, vec(r)),
    }))
    .sort((a, b) => b.similarite - a.similarite)
    .slice(0, n);
}

export type ProgressionJoueurRow = {
  saison_id: string;
  saison_courte: string;
  minutes: number;
  matchs_joues: number;
  buts_p90: number | null;
  xg_p90: number | null;
  passes_dec_p90: number | null;
  xag_p90: number | null;
  tirs_cadres_p90: number | null;
  key_passes_p90: number | null;
  dribbles_p90: number | null;
  tackles_p90: number | null;
  interceptions_p90: number | null;
  score_pepite_corrige: number | null;
  rating: number | null;
  nom_complet: string;
  nom_court: string | null;
};

// Portage de web/utils/db.py::get_progression_joueur() — ajout de
// j.nom_complet/nom_court (JOIN dim_joueurs) absent de la requête
// d'origine : côté Streamlit le nom venait de la session de recherche
// (player_progression_searchbox), pas de cette requête ; ici la page lit
// uniquement l'id depuis l'URL, donc le nom doit être résolu ici.
export async function getProgressionJoueur(joueurId: number): Promise<ProgressionJoueurRow[]> {
  const rows = await query`
    SELECT
      f.saison_id, s.saison_courte,
      f.minutes, f.matchs_joues,
      f.buts_p90, f.xg_p90, f.passes_dec_p90, f.xag_p90,
      f.tirs_cadres_p90, f.key_passes_p90,
      f.dribbles_p90, f.tackles_p90, f.interceptions_p90,
      f.score_pepite_corrige, f.rating,
      j.nom_complet, j.nom_court
    FROM public.fact_stats f
    JOIN public.dim_saisons s ON f.saison_id = s.saison_id
    JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
    WHERE f.joueur_id = ${joueurId}
    ORDER BY f.saison_id ASC
  `;
  return rows as ProgressionJoueurRow[];
}
