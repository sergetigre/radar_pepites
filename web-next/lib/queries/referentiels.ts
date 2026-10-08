import { query } from "@/lib/db";
import type { Ligue } from "@/lib/constants/postes";

export type { Ligue };

// Fichier SERVEUR UNIQUEMENT (importe lib/db.ts) — ne jamais importer ce
// module depuis un composant "use client", même pour un type ou une
// constante : voir lib/constants/postes.ts pour l'équivalent client-safe.

// Portage 1:1 de web/utils/db.py::get_ligues()
export async function getLigues(): Promise<Ligue[]> {
  const rows = await query`
    SELECT ligue_id, nom_complet, nom_court, pays, couleur_hex
    FROM public.dim_ligues ORDER BY rang_projet
  `;
  return rows as Ligue[];
}

// Portage 1:1 de web/utils/db.py::get_saisons()
export async function getSaisons(): Promise<string[]> {
  const rows = await query`
    SELECT saison_id FROM public.dim_saisons ORDER BY saison_id DESC
  `;
  return (rows as { saison_id: string }[]).map((r) => r.saison_id);
}

export type Nationalite = { nationalite_id: string; nom_fr: string };

// Pas d'équivalent côté web/ Streamlit (nouveau critère de recherche,
// page Championnats) — public.dim_nationalites fournit les noms FR pour
// les codes déjà utilisés ailleurs (dim_joueurs.nationalite_principale).
export async function getNationalites(): Promise<Nationalite[]> {
  const rows = await query`
    SELECT nationalite_id, nom_fr
    FROM public.dim_nationalites
    ORDER BY nom_fr
  `;
  return rows as Nationalite[];
}
