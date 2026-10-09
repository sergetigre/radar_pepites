import { getProgressionGk } from "@/lib/queries/gardiens";
import { SearchCombobox } from "@/components/ui/SearchCombobox";
import { ProgressionView } from "@/components/player/ProgressionView";
import { Icon } from "@/components/ui/Icon";
import type { Metric } from "@/components/charts/LineProgression";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary } from "@/lib/i18n/dictionaries";

// Portage 1:1 de web/pages/08_Progression_GK.py
export default async function ProgressionGkPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const t = getDictionary(await getLocale());
  const M = t.metricsShort;

  const METRIQUES_GK: Metric[] = [
    { col: "saves_p90", label: M.saves_p90, color: "#2DAD7E" },
    { col: "goals_prevented", label: M.goals_prevented, color: "#5DCBA0" },
  ];
  const DEFAULT_SELECTED = METRIQUES_GK.map((m) => m.label);

  const TABLE_COLS = [
    { col: "saison_courte", label: t.progression.colSeason },
    { col: "minutes", label: t.progression.colMinutes },
    { col: "matchs_joues", label: t.progression.colMatches },
    { col: "saves_p90", label: M.saves_p90, highlight: true },
    { col: "goals_prevented", label: M.goals_prevented, highlight: true },
    { col: "save_pct", label: t.metrics.pct_save_pct, highlight: true },
    { col: "clean_sheets_pct", label: `${t.metrics.pct_clean_sheets_pct} %`, highlight: true },
    { col: "score_pepite_corrige", label: t.explorer.colScore, highlight: true },
  ];

  const sp = await searchParams;
  const joueurIdRaw = typeof sp.joueur_id === "string" ? sp.joueur_id : undefined;

  const data = joueurIdRaw ? await getProgressionGk(Number(joueurIdRaw)) : [];
  const nom = data[0]?.nom_court || data[0]?.nom_complet || "";
  const label = data[0] ? `${data[0].nom_complet}` : "";

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-6 flex items-center gap-2">
        <Icon name="trending_up" size={28} />
        {t.progression.titleGk}
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
        <p className="text-text-muted">{t.progression.typeNameGk}</p>
      ) : data.length === 0 ? (
        <p className="text-warning">{t.progression.noData}</p>
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
