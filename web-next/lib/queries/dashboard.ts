import { query } from "@/lib/db";

export type Kpis = {
  nb: number;
  moy: number | null;
  max: number | null;
  ligues: number;
};

// Portage 1:1 de la requête get_kpis() inline dans
// web/pages/00_Tableau_de_bord.py
export async function getKpis(
  saison: string,
  ligues: string[],
  postes: string[],
  minMin: number,
  ageMax: number
): Promise<Kpis> {
  const rows = await query`
    SELECT
      COUNT(DISTINCT joueur_id)             as nb,
      ROUND(AVG(score_corrige)::numeric,1)  as moy,
      MAX(score_corrige)                    as max,
      COUNT(DISTINCT ligue_id)              as ligues
    FROM gold.vue_score_pepite_ranking
    WHERE est_u23=TRUE AND saison_id=${saison}
      AND minutes>=${minMin} AND age<=${ageMax}
      AND ligue_id = ANY(${ligues}) AND poste_id = ANY(${postes})
  `;
  const r = rows[0] as { nb: string | number; moy: string | number | null; max: string | number | null; ligues: string | number };
  return {
    nb: Number(r.nb),
    moy: r.moy === null ? null : Number(r.moy),
    max: r.max === null ? null : Number(r.max),
    ligues: Number(r.ligues),
  };
}

export type TopLigueRow = {
  joueur_id: number;
  joueur: string;
  poste_id: string;
  ligue: string;
  ligue_id: string;
  equipe: string;
  age: number;
  score_corrige: number;
  couleur_hex: string | null;
  team_id_ss: number | null;
  nationalite_principale: string | null;
};

// Portage de la requête top_par_ligue() inline dans
// web/pages/00_Tableau_de_bord.py — ajout de team_id_ss (logo club) et
// nationalite_principale (drapeau), même jointure que getClassement()
// (lib/queries/joueurs.ts).
export async function topParLigue(
  saison: string,
  ligues: string[],
  postes: string[],
  minMin: number,
  ageMax: number
): Promise<TopLigueRow[]> {
  const rows = await query`
    SELECT DISTINCT ON (r.ligue_id)
      r.joueur_id, r.joueur, r.poste_id, r.ligue, r.ligue_id,
      r.equipe, r.age, r.score_corrige, r.couleur_hex,
      r.nationalite_principale,
      e.team_id_ss
    FROM gold.vue_score_pepite_ranking r
    LEFT JOIN public.fact_stats f ON f.joueur_id = r.joueur_id AND f.saison_id = r.saison_id
    LEFT JOIN public.dim_equipes e ON e.equipe_id = f.equipe_id
    WHERE r.est_u23=TRUE AND r.saison_id=${saison}
      AND r.ligue_id = ANY(${ligues}) AND r.poste_id = ANY(${postes})
      AND r.minutes>=${minMin} AND r.age<=${ageMax}
    ORDER BY r.ligue_id, r.score_corrige DESC
  `;
  return rows as TopLigueRow[];
}
