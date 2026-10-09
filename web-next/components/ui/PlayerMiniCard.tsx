import Link from "next/link";
import type { TopLigueRow } from "@/lib/queries/dashboard";
import { formatNumber } from "@/lib/format";
import { ligueColor } from "@/lib/ligue-colors";
import { teamLogoUrl, ligueLogoUrl, ligueLogoInvert, flagImageUrl } from "@/lib/media";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { SafeImg } from "@/components/ui/SafeImg";

// Portage de la carte "pépite" cliquable de web/pages/00_Tableau_de_bord.py
// (render_html + classes .card/.player-mini-card) — ajout logo club + logo
// ligue (absents de l'original Streamlit) pour repérer d'un coup d'œil les
// clubs/ligues les plus représentés.
export async function PlayerMiniCard({ row, saison }: { row: TopLigueRow; saison: string }) {
  const t = getDictionary(await getLocale());
  const color = ligueColor(row.ligue_id);
  const clubUrl = teamLogoUrl(row.team_id_ss);
  const ligueUrl = ligueLogoUrl(row.ligue_id);
  const flagUrl = flagImageUrl(row.nationalite_principale);
  const posteLabel = row.poste_id
    ? t.postes.labels[row.poste_id as keyof typeof t.postes.labels] ?? row.poste_id
    : "";
  return (
    <Link
      href={`/radar-joueur?joueur_id=${row.joueur_id}&saison=${saison}`}
      className="player-card-link"
    >
      <div className="card card-accent player-mini-card" style={{ borderLeftColor: color }}>
        <div className="pmc-name">
          {flagUrl ? <SafeImg src={flagUrl} className="flag-icon" /> : "⚽"}
          {row.joueur}
        </div>
        <div className="pmc-league flex items-center gap-1 mt-1">
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
          {posteLabel} · {row.age} {t.common.years}
        </div>
        <span className="score-badge-sm">★ {formatNumber(row.score_corrige)}</span>
      </div>
    </Link>
  );
}
