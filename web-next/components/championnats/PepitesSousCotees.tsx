import Link from "next/link";
import type { ClassementRow } from "@/lib/queries/joueurs";
import { formatNumber } from "@/lib/format";
import { flagImageUrl, teamLogoUrl, ligueLogoUrl, ligueLogoInvert } from "@/lib/media";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { SafeImg } from "@/components/ui/SafeImg";

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
export async function PepitesSousCotees({ data, saison }: { data: ClassementRow[]; saison: string }) {
  const t = getDictionary(await getLocale());
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
    return <p className="text-text-muted text-sm">{t.championnats.noPepites}</p>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {pepites.map((row) => {
        const flagUrl = flagImageUrl(row.nationalite_principale);
        const clubUrl = teamLogoUrl(row.team_id_ss);
        const ligueUrl = ligueLogoUrl(row.ligue_id);
        const posteLabel = row.poste_id
          ? t.postes.labels[row.poste_id as keyof typeof t.postes.labels] ?? row.poste_id
          : "";
        return (
          <Link
            key={row.joueur_id}
            href={`/radar-joueur?joueur_id=${row.joueur_id}&saison=${saison}`}
            className="player-card-link"
          >
            <div className="card card-accent player-mini-card" style={{ borderLeftColor: "#5DCBA0" }}>
              <div className="pmc-name">
                💎
                <SafeImg src={flagUrl} className="flag-icon" />
                {row.joueur}
              </div>
              <div className="pmc-league flex items-center gap-1 mt-1">
                <span>{posteLabel} ·</span>
                <SafeImg src={clubUrl} className="club-logo" />
                <span>{row.equipe}</span>
              </div>
              <div className="pmc-league flex items-center gap-1 mt-0.5">
                <SafeImg
                  src={ligueUrl}
                  className={`ligue-logo${ligueLogoInvert(row.ligue_id) ? " ligue-logo-invert" : ""}`}
                />
                <span>{row.ligue}</span>
              </div>
              <div className="pmc-details">
                {row.age} {t.common.years} · {Math.trunc(row.minutes)} {t.common.minutesPlayed}
              </div>
              <span className="score-badge-sm">
                ★ {formatNumber(row.score_corrige)}
              </span>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
