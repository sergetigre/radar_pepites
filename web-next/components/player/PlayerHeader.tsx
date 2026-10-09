"use client";

import { flagImageUrl, playerPhotoUrl, teamLogoUrl, ligueLogoUrl, ligueLogoInvert } from "@/lib/media";
import { Icon } from "@/components/ui/Icon";
import { formatNumber } from "@/lib/format";
import { ligueColor } from "@/lib/ligue-colors";
import { useI18n } from "@/components/i18n/I18nProvider";

// Portage 1:1 de web/utils/components.py::ligue_court()
const LIGUE_COURT_MAP: Record<string, string> = {
  "Premier League": "PL",
  "La Liga": "Liga",
  Bundesliga: "BL",
  "Serie A": "SerA",
  "Ligue 1": "L1",
  "Primeira Liga": "PL PT",
  Eredivisie: "Ere",
  "Pro League": "JPL",
  "Süper Lig": "SL",
  "Bundesliga Autriche": "BL AT",
};

function ligueCourt(ligueNom: string | null | undefined): string {
  if (!ligueNom) return "—";
  return LIGUE_COURT_MAP[ligueNom] ?? ligueNom.slice(0, 3);
}

export type PlayerHeaderData = {
  nom_complet: string | null;
  age: number | null;
  nationalite_principale: string | null;
  taille_cm: number | null;
  pied_dominant: string | null;
  equipe: string | null;
  ligue: string | null;
  ligue_id: string | null;
  score_pepite_corrige: number | null;
  score_pepite: number | null;
  score_rang_ligue: number | null;
  score_rang_global: number | null;
  couleur_hex: string | null;
  player_id_ss: number | null;
  team_id_ss: number | null;
  poste_id?: string | null;
  poste_principal?: string | null;
  saison_id?: string | null;
  saison_courte?: string | null;
};

// Portage 1:1 de web/utils/components.py::render_player_header()
export function PlayerHeader({ row, isGk = false }: { row: PlayerHeaderData; isGk?: boolean }) {
  const { t } = useI18n();
  const nom = row.nom_complet || "—";
  const age = row.age;
  const nat = row.nationalite_principale;
  const taille = row.taille_cm;
  const pied = row.pied_dominant;
  const equipe = row.equipe || "—";
  const ligue = row.ligue || "—";
  const score = row.score_pepite_corrige ?? row.score_pepite;
  const rangL = row.score_rang_ligue;
  const rangG = row.score_rang_global;
  const color = ligueColor(row.ligue_id);
  const posteCode = row.poste_id || row.poste_principal || (isGk ? "GK" : "");
  const poste = posteCode
    ? t.postes.labels[posteCode as keyof typeof t.postes.labels] ?? posteCode
    : "";
  const saison = row.saison_courte || row.saison_id;

  const photoUrl = playerPhotoUrl(row.player_id_ss);
  const clubUrl = teamLogoUrl(row.team_id_ss);
  const ligueUrl = ligueLogoUrl(row.ligue_id);
  const flagUrl = flagImageUrl(nat);

  return (
    <div className="player-header">
      <div className="flex justify-between items-start flex-wrap gap-4">
        <div className="flex gap-4 flex-1 min-w-[200px]">
          {photoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={photoUrl}
              alt={nom}
              className="player-photo"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
          ) : (
            <div className="player-photo" />
          )}
          <div>
            <div
              className="text-[0.75rem] font-bold uppercase tracking-wide mb-1.5 flex items-center gap-1.5 flex-wrap"
              style={{ color }}
            >
              {clubUrl && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={clubUrl}
                  alt=""
                  className="club-logo"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              )}
              <span>{equipe}</span>
              <span className="opacity-60">·</span>
              {ligueUrl && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={ligueUrl}
                  alt=""
                  className={`ligue-logo${ligueLogoInvert(row.ligue_id) ? " ligue-logo-invert" : ""}`}
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              )}
              <span>{ligue}</span>
            </div>
            <div className="player-name">{nom}</div>
            <div className="my-2.5 flex flex-wrap">
              {saison && (
                <span className="player-badge">
                  <Icon name="event" size={14} />
                  {t.common.season} {saison}
                </span>
              )}
              {age != null && (
                <span className="player-badge">
                  <Icon name="cake" size={14} />
                  {age} {t.common.years}
                </span>
              )}
              {nat && (
                <span className="player-badge">
                  {flagUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={flagUrl}
                      alt=""
                      className="flag-icon"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                      }}
                    />
                  ) : (
                    <Icon name="flag" size={14} />
                  )}
                  {nat}
                </span>
              )}
              {taille != null && (
                <span className="player-badge">
                  <Icon name="height" size={14} />
                  {taille} cm
                </span>
              )}
              {pied && (
                <span className="player-badge">
                  <Icon name="sports_soccer" size={14} />
                  {pied}
                </span>
              )}
              {poste && (
                <span className="player-badge">
                  <Icon name="location_on" size={14} />
                  {poste}
                </span>
              )}
            </div>
          </div>
        </div>
        {score != null && (
          <div className="text-right">
            <div className="text-[0.65rem] text-text-muted mb-1 uppercase tracking-wide">
              Score Pépite
            </div>
            <div className="score-badge">{formatNumber(score)}</div>
            <div className="text-[0.72rem] text-text-muted mt-1.5">
              #{rangL ?? "—"} {ligueCourt(ligue)} · #{rangG ?? "—"} Global
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
