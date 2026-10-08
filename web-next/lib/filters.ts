import { ALL_POSTES } from "@/lib/constants/postes";

// Partagé Server Components (lecture SQL) / composant client Filters —
// aucune dépendance à lib/db.ts ici, donc importable des deux côtés.

export const MINUTES_OPTIONS = [90, 180, 270, 450, 900, 1350, 1800];
export const DEFAULT_MIN_MIN = 450;
export const DEFAULT_AGE_MAX = 23;

export type Filters = {
  saison: string;
  ligues: string[];
  postes: string[];
  minMin: number;
  ageMax: number;
};

export function getParam(
  searchParams: URLSearchParams | Record<string, string | string[] | undefined>,
  key: string
): string | undefined {
  return searchParams instanceof URLSearchParams
    ? (searchParams.get(key) ?? undefined)
    : ((Array.isArray(searchParams[key]) ? searchParams[key]?.[0] : searchParams[key]) as
        | string
        | undefined);
}

// Convention partagée par toutes les listes filtrables du site (ligues,
// postes, nationalités...) : param absent = tout coché (défaut), valeur
// "__none__" = bouton "Aucun", sinon liste CSV explicite.
export function parseList(raw: string | undefined, allValues: string[]): string[] {
  if (raw === undefined) return allValues;
  if (raw === "__none__") return [];
  return raw.split(",").filter(Boolean);
}

/**
 * Lit les filtres depuis l'URL (searchParams), avec les mêmes valeurs par
 * défaut que web/utils/sidebar.py::render_filters() : saison la plus
 * récente, toutes les ligues/tous les postes cochés, 450 min, 23 ans.
 * Utilisable côté serveur (Server Components des pages) comme côté client.
 */
export function parseFilters(
  searchParams: URLSearchParams | Record<string, string | string[] | undefined>,
  allLigueIds: string[],
  defaultSaison: string
): Filters {
  const get = (key: string) => getParam(searchParams, key);

  const saison = get("saison") ?? defaultSaison;
  const ligues = parseList(get("ligues"), allLigueIds);
  const postes = parseList(get("postes"), ALL_POSTES);
  const minMin = Number(get("min_min") ?? DEFAULT_MIN_MIN);
  const ageMax = Number(get("age_max") ?? DEFAULT_AGE_MAX);

  return { saison, ligues, postes, minMin, ageMax };
}
