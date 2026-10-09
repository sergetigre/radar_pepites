// Formatage des nombres décimaux à travers tout le site : 2 décimales
// partout, de façon cohérente (demande explicite utilisateur — le site
// mélangeait auparavant 1, 2 et 3 décimales selon les pages/colonnes).
// Les percentiles (PctBars) restent des entiers par design (comme
// Streamlit `{val:.0f}`), donc hors du champ de ce helper.
export function formatNumber(v: number | null | undefined, decimals = 2): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return v.toFixed(decimals);
}

// Équivalent côté client de unaccent() + LOWER() utilisé dans les requêtes
// SQL de recherche (lib/queries/search.ts) — pour les listes filtrées
// entièrement en JS (ex. ChampionnatFilters), où "e" doit aussi trouver
// "é", "è", "ê"...
export function unaccent(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}
