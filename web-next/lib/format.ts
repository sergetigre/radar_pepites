// Formatage des nombres décimaux à travers tout le site : 2 décimales
// partout, de façon cohérente (demande explicite utilisateur — le site
// mélangeait auparavant 1, 2 et 3 décimales selon les pages/colonnes).
// Les percentiles (PctBars) restent des entiers par design (comme
// Streamlit `{val:.0f}`), donc hors du champ de ce helper.
export function formatNumber(v: number | null | undefined, decimals = 2): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return v.toFixed(decimals);
}
