import { query } from "@/lib/db";

export type JoueurSearchResult = {
  joueur_id: number;
  joueur: string;
  equipe: string;
  ligue: string;
  ligue_id: string;
  poste_id: string;
  age: number;
  score_corrige: number | null;
  saison_id: string;
  joueur_saison: string;
};

// Portage de web/utils/db.py::search_joueurs() — deux écarts assumés par
// rapport au 1:1 : (1) recherche insensible aux accents via l'extension
// Postgres unaccent (ex. "Guela" trouve "Guéla Doué"), demandé
// explicitement par l'utilisateur après avoir constaté que Streamlit a la
// même limitation ; (2) ajout de "est_u23 = TRUE", absent côté Streamlit —
// gold.vue_score_pepite_ranking contient aussi les joueurs non-U23 (ex. le
// vrai Mohamed Salah, 34 ans), que la recherche remontait donc comme
// résultat sur un outil dédié aux U23.
export async function searchJoueurs(nom: string): Promise<JoueurSearchResult[]> {
  const rows = await query`
    SELECT DISTINCT
      joueur_id, joueur, equipe, ligue, ligue_id,
      poste_id, age, score_corrige, saison_id,
      CONCAT(joueur, ' — ', equipe, ' — ', saison_id) as joueur_saison
    FROM gold.vue_score_pepite_ranking
    WHERE est_u23 = TRUE
      AND unaccent(LOWER(joueur)) LIKE unaccent(LOWER(${"%" + nom + "%"}))
    ORDER BY joueur, saison_id DESC
    LIMIT 30
  `;
  return rows as JoueurSearchResult[];
}

export type GkSearchResult = {
  joueur_id: number;
  joueur: string;
  equipe: string;
  ligue_id: string;
  saison_id: string;
  joueur_saison: string;
};

// Portage de web/utils/db.py::search_gk() — mêmes écarts assumés que
// searchJoueurs() ci-dessus (unaccent + est_u23 = TRUE).
export async function searchGk(nom: string): Promise<GkSearchResult[]> {
  const rows = await query`
    SELECT DISTINCT
      f.joueur_id, j.nom_complet as joueur,
      e.nom_complet as equipe, f.ligue_id, f.saison_id,
      CONCAT(j.nom_complet, ' — ', e.nom_complet, ' — ', f.saison_id) as joueur_saison
    FROM public.fact_stats f
    JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
    JOIN public.dim_equipes e ON f.equipe_id = e.equipe_id
    WHERE f.poste_id = 'GK' AND f.est_u23 = TRUE
      AND unaccent(LOWER(j.nom_complet)) LIKE unaccent(LOWER(${"%" + nom + "%"}))
    ORDER BY j.nom_complet, f.saison_id DESC
    LIMIT 30
  `;
  return rows as GkSearchResult[];
}

export type UniqueSearchResult = { joueur_id: number; joueur: string };

// Portage de web/utils/db.py::search_joueurs_unique() — un résultat par
// joueur (toutes saisons confondues), utilisé par Progression où on choisit
// un joueur, pas une saison précise. Mêmes écarts assumés (unaccent +
// est_u23 = TRUE) que searchJoueurs() ci-dessus.
export async function searchJoueursUnique(nom: string): Promise<UniqueSearchResult[]> {
  const rows = await query`
    SELECT joueur_id, joueur FROM (
      SELECT DISTINCT ON (joueur_id) joueur_id, joueur, saison_id
      FROM gold.vue_score_pepite_ranking
      WHERE est_u23 = TRUE
        AND unaccent(LOWER(joueur)) LIKE unaccent(LOWER(${"%" + nom + "%"}))
      ORDER BY joueur_id, saison_id DESC
    ) t
    ORDER BY joueur
    LIMIT 30
  `;
  return rows as UniqueSearchResult[];
}

// Portage de web/utils/db.py::search_gk_unique() — équivalent gardien.
export async function searchGkUnique(nom: string): Promise<UniqueSearchResult[]> {
  const rows = await query`
    SELECT joueur_id, joueur FROM (
      SELECT DISTINCT ON (f.joueur_id)
        f.joueur_id, j.nom_complet as joueur, f.saison_id
      FROM public.fact_stats f
      JOIN public.dim_joueurs j ON f.joueur_id = j.joueur_id
      WHERE f.poste_id = 'GK' AND f.est_u23 = TRUE
        AND unaccent(LOWER(j.nom_complet)) LIKE unaccent(LOWER(${"%" + nom + "%"}))
      ORDER BY f.joueur_id, f.saison_id DESC
    ) t
    ORDER BY joueur
    LIMIT 30
  `;
  return rows as UniqueSearchResult[];
}
