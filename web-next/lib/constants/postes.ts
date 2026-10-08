// Constantes/types partagés côté serveur ET client — ce fichier ne doit
// JAMAIS importer lib/db.ts (ou tout module qui en dépend), sous peine de
// faire fuiter le client Neon dans le bundle navigateur (webpack embarque
// tout l'arbre d'import d'un "use client" dans le JS envoyé au navigateur).

export type Ligue = {
  ligue_id: string;
  nom_complet: string;
  nom_court: string;
  pays: string;
  couleur_hex: string | null;
};

// Portage 1:1 de web/utils/sidebar.py::FAMILLES_POSTES.
export const FAMILLES_POSTES: Record<string, Record<string, string>> = {
  Attaquants: { FW: "Avant-centre", LW: "Ailier gauche", RW: "Ailier droit" },
  Milieux: { AM: "Milieu offensif", CM: "Milieu central", DM: "Milieu défensif" },
  Défenseurs: { CB: "Défenseur central", LB: "Latéral gauche", RB: "Latéral droit" },
};

export const ALL_POSTES = Object.values(FAMILLES_POSTES).flatMap((f) =>
  Object.keys(f)
);
