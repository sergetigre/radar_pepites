import { getGkFiche, type GkFiche } from "@/lib/queries/gardiens";
import { SearchCombobox } from "@/components/ui/SearchCombobox";
import { RadarCompare } from "@/components/charts/RadarCompare";
import { ComparisonStatsTable } from "@/components/player/ComparisonStatsTable";
import { RADAR_AXES } from "@/lib/charts-config";
import { Icon } from "@/components/ui/Icon";

const STATS_GK_TABLEAU = [
  { label: "Score Pépite ★", col: "score_pepite_corrige" },
  { label: "Arrêts/90", col: "saves_p90" },
  { label: "Buts évités", col: "goals_prevented" },
  { label: "% Arrêts", col: "save_pct" },
  { label: "Clean sheets %", col: "clean_sheets_pct" },
  { label: "Passes longues %", col: "long_balls_pct" },
  { label: "Minutes", col: "minutes", integer: true },
  { label: "Matchs", col: "matchs_joues", integer: true },
];

// Portage 1:1 de web/pages/07_Comparaison_GK.py
export default async function ComparaisonGkPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const getStr = (k: string) => (typeof sp[k] === "string" ? (sp[k] as string) : undefined);
  const idARaw = getStr("joueur_a");
  const saisonA = getStr("saison_a");
  const idBRaw = getStr("joueur_b");
  const saisonB = getStr("saison_b");

  let rowA: GkFiche | null = null;
  let rowB: GkFiche | null = null;
  if (idARaw && saisonA) rowA = await getGkFiche(Number(idARaw), saisonA);
  if (idBRaw && saisonB) rowB = await getGkFiche(Number(idBRaw), saisonB);

  const labelA = rowA ? `${rowA.nom_complet} — ${rowA.equipe} — ${saisonA}` : "";
  const labelB = rowB ? `${rowB.nom_complet} — ${rowB.equipe} — ${saisonB}` : "";

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-6 flex items-center gap-2">
        <Icon name="compare_arrows" size={28} />
        Comparaison Gardiens
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-[5fr_1fr_5fr] gap-4 items-start">
        <div>
          <div className="text-primary font-bold mb-2.5">GK A</div>
          <SearchCombobox
            kind="gardiens"
            placeholder="Ex: Donnarumma"
            defaultValue={labelA}
            idParam="joueur_a"
            saisonParam="saison_a"
          />
        </div>
        <div className="flex items-center justify-center text-text-muted text-xl py-1 lg:pt-10">vs</div>
        <div>
          <div className="text-danger font-bold mb-2.5">GK B</div>
          <SearchCombobox
            kind="gardiens"
            placeholder="Ex: Donnarumma"
            defaultValue={labelB}
            idParam="joueur_b"
            saisonParam="saison_b"
          />
        </div>
      </div>

      {!idARaw || !idBRaw ? (
        <p className="text-text-muted mt-6">
          Sélectionnez les deux gardiens pour lancer la comparaison.
        </p>
      ) : !rowA || !rowB ? (
        <p className="text-warning mt-6">Données insuffisantes.</p>
      ) : (
        <>
          <hr className="border-border my-6" />
          <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
            <Icon name="radar" size={18} />
            Comparaison radar
          </h4>
          <RadarCompare
            rowA={rowA}
            rowB={rowB}
            axes={RADAR_AXES["GK"]}
            nameA={`${rowA.nom_court || "GK A"} — ${saisonA}`}
            nameB={`${rowB.nom_court || "GK B"} — ${saisonB}`}
          />

          <hr className="border-border my-6" />
          <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
            <Icon name="table_chart" size={18} />
            Statistiques détaillées
          </h4>
          <ComparisonStatsTable
            stats={STATS_GK_TABLEAU}
            rowA={rowA}
            rowB={rowB}
            nameA={`${rowA.nom_court || "GK A"} — ${saisonA}`}
            nameB={`${rowB.nom_court || "GK B"} — ${saisonB}`}
          />
        </>
      )}
    </div>
  );
}
