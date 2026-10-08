import Link from "next/link";
import type { TopLigueRow } from "@/lib/queries/dashboard";
import { formatNumber } from "@/lib/format";
import { ligueColor } from "@/lib/ligue-colors";

// Portage 1:1 de la carte "pépite" cliquable de
// web/pages/00_Tableau_de_bord.py (render_html + classes .card/.player-mini-card).
export function PlayerMiniCard({ row, saison }: { row: TopLigueRow; saison: string }) {
  const color = ligueColor(row.ligue_id);
  return (
    <Link
      href={`/radar-joueur?joueur_id=${row.joueur_id}&saison=${saison}`}
      className="player-card-link"
    >
      <div className="card card-accent player-mini-card" style={{ borderLeftColor: color }}>
        <div className="pmc-name">⚽ {row.joueur}</div>
        <div className="pmc-league">{row.ligue}</div>
        <div className="pmc-details">
          {row.equipe} · {row.poste_id} · {row.age} ans
        </div>
        <span className="score-badge-sm">★ {formatNumber(row.score_corrige)}</span>
      </div>
    </Link>
  );
}
