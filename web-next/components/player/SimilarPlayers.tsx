import Link from "next/link";
import { Icon } from "@/components/ui/Icon";
import type { SimilarPlayer } from "@/lib/queries/joueurs";

// Portage de web/utils/components.py::render_similar_players() — chaque
// carte ouvre le radar du joueur correspondant (ajout vs. l'original, qui
// était non cliquable côté Streamlit).
export function SimilarPlayers({
  players,
  saison,
}: {
  players: SimilarPlayer[];
  saison: string;
}) {
  return (
    <div>
      <div className="text-[0.7rem] font-bold uppercase tracking-[2px] text-text-muted mb-2.5 flex items-center gap-1">
        <Icon name="group" />
        Profils similaires
      </div>
      {players.length === 0 ? (
        <p className="text-text-muted text-sm">Données insuffisantes.</p>
      ) : (
        players.map((p) => (
          <Link
            key={p.joueur_id}
            href={`/radar-joueur?joueur_id=${p.joueur_id}&saison=${saison}`}
            className="similar-card similar-card-link"
          >
            <div>
              <div className="font-semibold text-[0.9rem]">{p.joueur}</div>
              <div className="text-[0.75rem] text-text-muted">
                {p.equipe} · {p.ligue}
              </div>
            </div>
            <div className="similar-pct">{Math.trunc(p.similarite * 100)}%</div>
          </Link>
        ))
      )}
    </div>
  );
}
