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
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary, type Dictionary } from "@/lib/i18n/dictionaries";

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
  const t = getDictionary(await getLocale());

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-5 flex items-center gap-2">
        <Icon name="radar" size={28} />
        {t.radar.titlePlayer}
      </h1>

      <div className="mb-6">
        <SearchCombobox
          kind="joueurs"
          placeholder={t.radar.searchPlaceholderPlayer}
          defaultValue={prefill}
        />
      </div>

      {!joueurIdRaw ? (
        <p className="text-text-muted">{t.radar.typeNamePlayer}</p>
      ) : (
        <JoueurProfile joueurId={Number(joueurIdRaw)} saisonParam={saisonRaw} t={t} />
      )}
    </div>
  );
}

async function JoueurProfile({
  joueurId,
  saisonParam,
  t,
}: {
  joueurId: number;
  saisonParam?: string;
  t: Dictionary;
}) {
  const saisons = await getSaisons();
  const saison = saisonParam ?? saisons[0] ?? "";
  const row = await getJoueurFiche(joueurId, saison);

  if (!row) {
    return <p className="text-warning">{t.radar.noDataSelection}</p>;
  }

  const poste = row.poste_id || row.poste_principal || "CM";
  const nomCourt = row.nom_court || row.nom_complet || "Joueur";
  const color = ligueColor(row.ligue_id);

  const dfSim = await getProfilsSimilaires(joueurId, saison, poste);

  const catOffensif = {
    [t.metrics.pct_goals_p90]: row.pct_goals_p90,
    [t.metrics.pct_xg_p90]: row.pct_xg_p90,
    [t.metrics.pct_assists_p90]: row.pct_assists_p90,
    [t.metrics.pct_xag_p90]: row.pct_xag_p90,
    [t.metrics.pct_shots_p90]: row.pct_shots_p90,
  };
  const catPasses = {
    [t.metrics.pct_key_passes_p90]: row.pct_key_passes_p90,
    [t.metrics.pct_passes_pct]: row.pct_passes_pct,
    [t.metrics.pct_dribbles_p90]: row.pct_dribbles_p90,
  };
  const catDefense = {
    [t.metrics.pct_tackles_p90]: row.pct_tackles_p90,
    [t.metrics.pct_interceptions_p90]: row.pct_interceptions_p90,
    [t.metrics.pct_degagements_p90]: row.pct_degagements_p90,
    [t.metrics.pct_duels_aeriens_pct]: row.pct_duels_aeriens_pct,
  };

  return (
    <>
      <PlayerHeader row={row} />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr_1fr] gap-8">
        <div>
          <div className="text-[0.65rem] font-bold uppercase tracking-[2px] text-text-muted mb-2.5 flex items-center gap-1">
            <Icon name="sports_soccer" size={14} />
            {t.radar.position}
          </div>
          <div className="pitch-container">
            <TerrainSvg poste={poste} width={150} />
          </div>
          <div className="text-center text-[0.8rem] text-primary mt-2 font-semibold">
            {t.postes.labels[poste as keyof typeof t.postes.labels] ?? poste}
          </div>
        </div>

        <div>
          <RadarSingle row={row} poste={poste} name={nomCourt} color={color} labels={t.metrics} />
        </div>

        <div>
          <SimilarPlayers players={dfSim} saison={saison} />
        </div>
      </div>

      <hr className="border-border my-6" />
      <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
        <Icon name="bar_chart" size={18} />
        {t.radar.percentilesByCategory}
      </h4>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <PctBars metrics={catOffensif} title={`⚽ ${t.radar.offensive}`} />
        <PctBars metrics={catPasses} title={`🎯 ${t.radar.passing}`} />
        <PctBars metrics={catDefense} title={`🛡️ ${t.radar.defense}`} />
      </div>

      <hr className="border-border my-6" />
      <StrengthsWeaknesses row={row} />
    </>
  );
}
