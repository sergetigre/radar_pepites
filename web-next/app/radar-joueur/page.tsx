import { getSaisons } from "@/lib/queries/referentiels";
import { getJoueurFiche, getProfilsSimilaires } from "@/lib/queries/joueurs";
import { PlayerHeader } from "@/components/player/PlayerHeader";
import { TerrainSvg } from "@/components/player/TerrainSvg";
import { RadarSingle } from "@/components/charts/RadarSingle";
import { PctBars } from "@/components/player/PctBars";
import { StrengthsWeaknesses } from "@/components/player/StrengthsWeaknesses";
import { SimilarPlayers } from "@/components/player/SimilarPlayers";
import { SearchCombobox } from "@/components/ui/SearchCombobox";
import { Icon } from "@/components/ui/Icon";
import { ligueColor } from "@/lib/ligue-colors";

// Portage 1:1 de web/pages/02_Radar_Joueur.py
export default async function RadarJoueurPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const joueurIdRaw = typeof sp.joueur_id === "string" ? sp.joueur_id : undefined;
  const saisonRaw = typeof sp.saison === "string" ? sp.saison : undefined;
  const prefill = typeof sp.prefill === "string" ? sp.prefill : undefined;

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-5 flex items-center gap-2">
        <Icon name="radar" size={28} />
        Radar Joueur
      </h1>

      <div className="mb-6">
        <SearchCombobox
          kind="joueurs"
          placeholder="Ex : Saka, Wirtz, Yamal..."
          defaultValue={prefill}
        />
      </div>

      {!joueurIdRaw ? (
        <p className="text-text-muted">
          Tapez le nom d&apos;un joueur pour afficher son profil (2 lettres min.).
        </p>
      ) : (
        <JoueurProfile joueurId={Number(joueurIdRaw)} saisonParam={saisonRaw} />
      )}
    </div>
  );
}

async function JoueurProfile({
  joueurId,
  saisonParam,
}: {
  joueurId: number;
  saisonParam?: string;
}) {
  const saisons = await getSaisons();
  const saison = saisonParam ?? saisons[0] ?? "";
  const row = await getJoueurFiche(joueurId, saison);

  if (!row) {
    return <p className="text-warning">Données non disponibles pour cette sélection.</p>;
  }

  const poste = row.poste_id || row.poste_principal || "CM";
  const nomCourt = row.nom_court || row.nom_complet || "Joueur";
  const color = ligueColor(row.ligue_id);

  const dfSim = await getProfilsSimilaires(joueurId, saison, poste);

  const catOffensif = {
    "Buts/90": row.pct_goals_p90,
    "xG/90": row.pct_xg_p90,
    "Assists/90": row.pct_assists_p90,
    "xAG/90": row.pct_xag_p90,
    "Tirs/90": row.pct_shots_p90,
  };
  const catPasses = {
    "Key Passes/90": row.pct_key_passes_p90,
    "Précision pass": row.pct_passes_pct,
    "Dribbles/90": row.pct_dribbles_p90,
  };
  const catDefense = {
    "Tacles/90": row.pct_tackles_p90,
    "Interceptions/90": row.pct_interceptions_p90,
    "Dégagements/90": row.pct_degagements_p90,
    "Duels aériens": row.pct_duels_aeriens_pct,
  };

  return (
    <>
      <PlayerHeader row={row} />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr_1fr] gap-8">
        <div>
          <div className="text-[0.65rem] font-bold uppercase tracking-[2px] text-text-muted mb-2.5 flex items-center gap-1">
            <Icon name="sports_soccer" size={14} />
            Position
          </div>
          <div className="pitch-container">
            <TerrainSvg poste={poste} width={150} />
          </div>
          <div className="text-center text-[0.8rem] text-primary mt-2 font-semibold">{poste}</div>
        </div>

        <div>
          <RadarSingle row={row} poste={poste} name={nomCourt} color={color} />
        </div>

        <div>
          <SimilarPlayers players={dfSim} saison={saison} />
        </div>
      </div>

      <hr className="border-border my-6" />
      <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
        <Icon name="bar_chart" size={18} />
        Percentiles par catégorie
      </h4>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <PctBars metrics={catOffensif} title="⚽ Offensif" />
        <PctBars metrics={catPasses} title="🎯 Passes" />
        <PctBars metrics={catDefense} title="🛡️ Défense" />
      </div>

      <hr className="border-border my-6" />
      <StrengthsWeaknesses row={row} />
    </>
  );
}
