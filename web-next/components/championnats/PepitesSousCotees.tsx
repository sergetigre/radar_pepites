import Link from "next/link";
import type { ClassementRow } from "@/lib/queries/joueurs";
import { formatNumber } from "@/lib/format";

// Interpolation linéaire — réplique pandas/numpy Series.quantile() par
// défaut (method="linear"), NaN exclus au préalable par l'appelant.
function quantile(sortedAsc: number[], q: number): number {
  const n = sortedAsc.length;
  if (n === 0) return NaN;
  if (n === 1) return sortedAsc[0];
  const pos = (n - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  const next = sortedAsc[base + 1];
  return next !== undefined ? sortedAsc[base] + rest * (next - sortedAsc[base]) : sortedAsc[base];
}

// Portage 1:1 de la section "Pépites sous-cotées" de
// web/pages/09_Championnats.py : Score Pépite dans le top 20% du
// championnat mais minutes jouées sous la médiane.
export function PepitesSousCotees({ data, saison }: { data: ClassementRow[]; saison: string }) {
  const scores = data
    .map((r) => r.score_corrige)
    .filter((v): v is number => v != null)
    .sort((a, b) => a - b);
  const minutes = data.map((r) => r.minutes).filter((v): v is number => v != null).sort((a, b) => a - b);

  const seuilScore = quantile(scores, 0.8);
  const medianeMinutes = quantile(minutes, 0.5);

  const pepites = data
    .filter(
      (r) => r.score_corrige != null && r.score_corrige >= seuilScore && r.minutes < medianeMinutes
    )
    .sort((a, b) => (b.score_corrige as number) - (a.score_corrige as number))
    .slice(0, 6);

  if (pepites.length === 0) {
    return (
      <p className="text-text-muted text-sm">
        Aucune pépite sous-cotée identifiée avec les filtres actuels.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {pepites.map((row) => (
        <Link
          key={row.joueur_id}
          href={`/radar-joueur?joueur_id=${row.joueur_id}&saison=${saison}`}
          className="player-card-link"
        >
          <div className="card card-accent player-mini-card" style={{ borderLeftColor: "#5DCBA0" }}>
            <div className="pmc-name">💎 {row.joueur}</div>
            <div className="pmc-league">
              {row.poste_id} · {row.equipe}
            </div>
            <div className="pmc-details">
              {row.age} ans · {Math.trunc(row.minutes)} min jouées
            </div>
            <span className="score-badge-sm">
              ★ {formatNumber(row.score_corrige)}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}
