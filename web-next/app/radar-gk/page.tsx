import { getSaisons } from "@/lib/queries/referentiels";
import { getGkFiche } from "@/lib/queries/gardiens";
import { PlayerHeader } from "@/components/player/PlayerHeader";
import { TerrainSvg } from "@/components/player/TerrainSvg";
import { RadarSingle } from "@/components/charts/RadarSingle";
import { PctBars } from "@/components/player/PctBars";
import { StrengthsWeaknesses } from "@/components/player/StrengthsWeaknesses";
import { SearchCombobox } from "@/components/ui/SearchCombobox";
import { Icon } from "@/components/ui/Icon";
import { ligueColor } from "@/lib/ligue-colors";

// Portage 1:1 de web/pages/06_Radar_GK.py
export default async function RadarGkPage({
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
        Radar Gardien
      </h1>

      <div className="mb-6">
        <SearchCombobox
          kind="gardiens"
          placeholder="Ex : Donnarumma junior..."
          defaultValue={prefill}
        />
      </div>

      {!joueurIdRaw ? (
        <p className="text-text-muted">
          Tapez le nom d&apos;un gardien pour afficher son profil (2 lettres min.).
        </p>
      ) : (
        <GkProfile joueurId={Number(joueurIdRaw)} saisonParam={saisonRaw} />
      )}
    </div>
  );
}

async function GkProfile({ joueurId, saisonParam }: { joueurId: number; saisonParam?: string }) {
  const saisons = await getSaisons();
  const saison = saisonParam ?? saisons[0] ?? "";
  const row = await getGkFiche(joueurId, saison);

  if (!row) {
    return <p className="text-warning">Données non disponibles pour cette sélection.</p>;
  }

  const nomGk = row.nom_court || row.nom_complet || "Gardien";
  const color = ligueColor(row.ligue_id);

  const metrics = {
    "Arrêts/90": row.pct_saves_p90,
    "Buts évités": row.pct_goals_prevented,
    "% Arrêts": row.pct_save_pct,
    "Clean sheets %": row.pct_clean_sheets_pct,
    "Passes longues %": row.pct_long_balls_pct,
  };

  return (
    <>
      <PlayerHeader row={row} isGk />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_2fr] gap-8">
        <div className="pitch-container">
          <TerrainSvg poste="GK" width={150} />
        </div>
        <div>
          <RadarSingle row={row} poste="GK" name={nomGk} color={color} />
        </div>
      </div>

      <hr className="border-border my-6" />
      <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
        <Icon name="bar_chart" size={18} />
        Percentiles
      </h4>

      {!row.has_fbref_data && (
        <p className="text-text-muted text-sm mb-2">
          ℹ️ % Arrêts et Clean sheets % (source fbref) non disponibles pour cette ligue.
        </p>
      )}
      <PctBars metrics={metrics} />

      <hr className="border-border my-6" />
      <StrengthsWeaknesses row={row} />
    </>
  );
}
