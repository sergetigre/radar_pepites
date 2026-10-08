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
};

// Portage 1:1 de la requête top_par_ligue() inline dans
// web/pages/00_Tableau_de_bord.py
export async function topParLigue(
  saison: string,
  ligues: string[],
  postes: string[],
  minMin: number,
  ageMax: number
): Promise<TopLigueRow[]> {
  const rows = await query`
    SELECT DISTINCT ON (ligue_id)
      joueur_id, joueur, poste_id, ligue, ligue_id,
      equipe, age, score_corrige, couleur_hex
    FROM gold.vue_score_pepite_ranking
    WHERE est_u23=TRUE AND saison_id=${saison}
      AND ligue_id = ANY(${ligues}) AND poste_id = ANY(${postes})
      AND minutes>=${minMin} AND age<=${ageMax}
    ORDER BY ligue_id, score_corrige DESC
  `;
  return rows as TopLigueRow[];
}
