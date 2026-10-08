import Link from "next/link";
import { formatNumber } from "@/lib/format";

type PlayerLike = {
  joueur_id: number;
  joueur: string;
  equipe: string;
  age: number;
  score_corrige: number | null;
};

// Portage 1:1 de web/pages/09_Championnats.py::carte_formation() —
// titulaire mis en avant (équipe, âge, Score Pépite), doublures
// compactes en dessous, toutes cliquables vers leur fiche.
export function FormationCard({
  players,
  urlBase,
  posteLabel,
  saison,
}: {
  players: PlayerLike[];
  urlBase: string;
  posteLabel: string;
  saison: string;
}) {
  if (players.length === 0) {
    return (
      <div
        className="card text-center"
        style={{ padding: "10px 12px", minWidth: 150 }}
      >
        <div className="font-bold text-white text-[0.85rem]">—</div>
        <div className="text-[0.68rem] text-text-muted mt-0.5">{posteLabel || "Indisponible"}</div>
      </div>
    );
  }

  const [titulaire, ...doublures] = players;

  return (
    <div className="card" style={{ padding: "10px 12px", minWidth: 160, maxWidth: 190 }}>
      <Link href={`${urlBase}?joueur_id=${titulaire.joueur_id}&saison=${saison}`} className="no-underline block">
        <div className="font-bold text-white text-[0.86rem] whitespace-nowrap overflow-hidden text-ellipsis">
          {titulaire.joueur}
        </div>
        <div className="text-[0.7rem] text-text-muted" style={{ margin: "2px 0 6px 0" }}>
          {titulaire.equipe} · {titulaire.age} ans
        </div>
        <span className="score-badge-sm">
          ★ {formatNumber(titulaire.score_corrige)}
        </span>
      </Link>
      {doublures.map((d) => (
        <Link
          key={d.joueur_id}
          href={`${urlBase}?joueur_id=${d.joueur_id}&saison=${saison}`}
          className="no-underline block"
        >
          <div
            className="border-t border-border"
            style={{ paddingTop: 5, marginTop: 5 }}
          >
            <div className="text-[0.72rem] font-semibold text-text-nav whitespace-nowrap overflow-hidden text-ellipsis">
              {d.joueur}
            </div>
            <div className="text-[0.64rem] text-text-muted whitespace-nowrap overflow-hidden text-ellipsis">
              {d.equipe} · {d.age} ans ·{" "}
              <span className="text-primary font-bold">
                ★ {formatNumber(d.score_corrige)}
              </span>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
