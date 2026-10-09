import Link from "next/link";
import { Icon } from "@/components/ui/Icon";
import type { SimilarPlayer } from "@/lib/queries/joueurs";
import { teamLogoUrl, ligueLogoUrl, ligueLogoInvert } from "@/lib/media";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary } from "@/lib/i18n/dictionaries";
import { SafeImg } from "@/components/ui/SafeImg";

// Portage de web/utils/components.py::render_similar_players() — chaque
// carte ouvre le radar du joueur correspondant (ajout vs. l'original, qui
// était non cliquable côté Streamlit).
export async function SimilarPlayers({
  players,
  saison,
}: {
  players: SimilarPlayer[];
  saison: string;
}) {
  const t = getDictionary(await getLocale());
  return (
    <div>
      <div className="text-[0.7rem] font-bold uppercase tracking-[2px] text-text-muted mb-2.5 flex items-center gap-1">
        <Icon name="group" />
        {t.radar.similarProfiles}
      </div>
      {players.length === 0 ? (
        <p className="text-text-muted text-sm">{t.common.insufficientData}</p>
      ) : (
        players.map((p) => {
          const clubUrl = teamLogoUrl(p.team_id_ss);
          const ligueUrl = ligueLogoUrl(p.ligue_id);
          return (
            <Link
              key={p.joueur_id}
              href={`/radar-joueur?joueur_id=${p.joueur_id}&saison=${saison}`}
              className="similar-card similar-card-link"
            >
              <div>
                <div className="font-semibold text-[0.9rem]">{p.joueur}</div>
                <div className="flex items-center gap-1 text-[0.75rem] text-text-muted mt-0.5">
                  <SafeImg src={clubUrl} className="club-logo" />
                  <span>{p.equipe}</span>
                </div>
                <div className="flex items-center gap-1 text-[0.75rem] text-text-muted mt-0.5">
                  <SafeImg
                    src={ligueUrl}
                    className={`ligue-logo${ligueLogoInvert(p.ligue_id) ? " ligue-logo-invert" : ""}`}
                  />
                  <span>{p.ligue}</span>
                </div>
              </div>
              <div className="similar-pct">{Math.trunc(p.similarite * 100)}%</div>
            </Link>
          );
        })
      )}
    </div>
  );
}
