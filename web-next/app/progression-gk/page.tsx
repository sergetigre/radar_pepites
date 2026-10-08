import { getProgressionGk } from "@/lib/queries/gardiens";
import { SearchCombobox } from "@/components/ui/SearchCombobox";
import { ProgressionView } from "@/components/player/ProgressionView";
import { Icon } from "@/components/ui/Icon";
import type { Metric } from "@/components/charts/LineProgression";

const METRIQUES_GK: Metric[] = [
  { col: "saves_p90", label: "Arrêts/90", color: "#2DAD7E" },
  { col: "goals_prevented", label: "Buts évités", color: "#5DCBA0" },
];
const DEFAULT_SELECTED = METRIQUES_GK.map((m) => m.label);

const TABLE_COLS = [
  { col: "saison_courte", label: "Saison" },
  { col: "minutes", label: "Minutes" },
  { col: "matchs_joues", label: "Matchs" },
  { col: "saves_p90", label: "Arrêts/90", highlight: true },
  { col: "goals_prevented", label: "Buts évités", highlight: true },
  { col: "save_pct", label: "% Arrêts", highlight: true },
  { col: "clean_sheets_pct", label: "Clean sheets %", highlight: true },
  { col: "score_pepite_corrige", label: "Score ★", highlight: true },
];

// Portage 1:1 de web/pages/08_Progression_GK.py
export default async function ProgressionGkPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const joueurIdRaw = typeof sp.joueur_id === "string" ? sp.joueur_id : undefined;

  const data = joueurIdRaw ? await getProgressionGk(Number(joueurIdRaw)) : [];
  const nom = data[0]?.nom_court || data[0]?.nom_complet || "";
  const label = data[0] ? `${data[0].nom_complet}` : "";

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-6 flex items-center gap-2">
        <Icon name="trending_up" size={28} />
        Progression Gardien
      </h1>

      <div className="mb-6">
        <SearchCombobox
          kind="gardiens"
          placeholder="Ex : Donnarumma junior..."
          defaultValue={label}
          unique
        />
      </div>

      {!joueurIdRaw ? (
        <p className="text-text-muted">
          Tapez le nom d&apos;un gardien pour afficher sa progression (2 lettres min.).
        </p>
      ) : data.length === 0 ? (
        <p className="text-warning">Aucune donnée de progression disponible.</p>
      ) : (
        <ProgressionView
          data={data}
          joueur={nom}
          metricsDefault={METRIQUES_GK}
          defaultSelectedLabels={DEFAULT_SELECTED}
          tableCols={TABLE_COLS}
          fbrefNotice
        />
      )}
    </div>
  );
}
