import { formatNumber } from "@/lib/format";

// integer: true pour les décomptes bruts (Minutes, Matchs) — pas de
// décimales à forcer dessus, contrairement aux stats /90 et au score.
type StatDef = { label: string; col: string; integer?: boolean };

// Portage 1:1 des tableaux "Statistiques détaillées" de
// web/pages/03_Comparaison.py / 07_Comparaison_GK.py. `showBetter` porte le
// marqueur 🟢 sur la valeur la plus haute — présent côté joueurs de champ
// uniquement, absent côté gardiens (fidèle à l'asymétrie du code source).
export function ComparisonStatsTable({
  stats,
  rowA,
  rowB,
  nameA,
  nameB,
  decimals = 2,
  showBetter = false,
  statLabel = "Stat",
}: {
  stats: StatDef[];
  rowA: Record<string, unknown>;
  rowB: Record<string, unknown>;
  nameA: string;
  nameB: string;
  decimals?: number;
  showBetter?: boolean;
  statLabel?: string;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-2 pr-4 text-text-muted font-semibold">{statLabel}</th>
            <th className="text-left py-2 pr-4 text-text-muted font-semibold">{nameA}</th>
            <th className="text-left py-2 text-text-muted font-semibold">{nameB}</th>
          </tr>
        </thead>
        <tbody>
          {stats.map(({ label, col, integer }) => {
            const rawA = typeof rowA[col] === "number" ? (rowA[col] as number) : null;
            const rawB = typeof rowB[col] === "number" ? (rowB[col] as number) : null;
            const validA = rawA != null && Number.isFinite(rawA);
            const validB = rawB != null && Number.isFinite(rawB);
            const betterA = showBetter && validA && validB && (rawA as number) > (rawB as number);
            const betterB = showBetter && validA && validB && (rawB as number) > (rawA as number);
            const fmt = (v: number | null | undefined) =>
              integer ? (v != null && Number.isFinite(v) ? String(Math.round(v)) : "—") : formatNumber(v, decimals);
            return (
              <tr key={col} className="border-b border-border/50">
                <td className="py-1.5 pr-4 text-text-nav">{label}</td>
                <td className="py-1.5 pr-4 tabular-nums">
                  {betterA && "🟢 "}
                  {fmt(rawA)}
                </td>
                <td className="py-1.5 tabular-nums">
                  {betterB && "🟢 "}
                  {fmt(rawB)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
