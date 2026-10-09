import { getProgressionJoueur } from "@/lib/queries/joueurs";
import { SearchCombobox } from "@/components/ui/SearchCombobox";
import { ProgressionView } from "@/components/player/ProgressionView";
import { Icon } from "@/components/ui/Icon";
import type { Metric } from "@/components/charts/LineProgression";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary } from "@/lib/i18n/dictionaries";

// Portage 1:1 de web/pages/04_Progression.py
export default async function ProgressionPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const t = getDictionary(await getLocale());
  const M = t.metricsShort;

  const METRIQUES_DEFAUT: Metric[] = [
    { col: "buts_p90", label: M.buts_p90, color: "#2DAD7E" },
    { col: "xg_p90", label: M.xg_p90, color: "#5DCBA0" },
    { col: "passes_dec_p90", label: M.passes_dec_p90, color: "#E0B452" },
    { col: "key_passes_p90", label: M.key_passes_p90, color: "#4ECDC4" },
    { col: "dribbles_p90", label: M.dribbles_p90, color: "#FF6B35" },
    { col: "tackles_p90", label: M.tackles_p90, color: "#E05252" },
  ];
  const DEFAULT_SELECTED = [M.buts_p90, M.xg_p90, M.passes_dec_p90];

  const TABLE_COLS = [
    { col: "saison_courte", label: t.progression.colSeason },
    { col: "minutes", label: t.progression.colMinutes },
    { col: "matchs_joues", label: t.progression.colMatches },
    { col: "buts_p90", label: M.buts_p90, highlight: true },
    { col: "xg_p90", label: M.xg_p90, highlight: true },
    { col: "passes_dec_p90", label: M.passes_dec_p90, highlight: true },
    { col: "xag_p90", label: "xAG/90", highlight: true },
    { col: "key_passes_p90", label: M.key_passes_p90, highlight: true },
    { col: "dribbles_p90", label: M.dribbles_p90, highlight: true },
    { col: "tackles_p90", label: M.tackles_p90, highlight: true },
    { col: "interceptions_p90", label: M.interceptions_p90, highlight: true },
    { col: "score_pepite_corrige", label: t.explorer.colScore, highlight: true },
  ];

  const sp = await searchParams;
  const joueurIdRaw = typeof sp.joueur_id === "string" ? sp.joueur_id : undefined;

  const data = joueurIdRaw ? await getProgressionJoueur(Number(joueurIdRaw)) : [];
  const nom = data[0]?.nom_court || data[0]?.nom_complet || "";
  const label = data[0] ? `${data[0].nom_complet}` : "";

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-2 flex items-center gap-2">
        <Icon name="trending_up" size={28} />
        {t.progression.title}
      </h1>
      <p className="text-text-muted text-sm mb-6">{t.progression.subtitle}</p>

      <div className="mb-6">
        <SearchCombobox
          kind="joueurs"
          placeholder="Ex : Saka, Wirtz, Yamal..."
          defaultValue={label}
          unique
        />
      </div>

      {!joueurIdRaw ? (
        <p className="text-text-muted">{t.progression.typeNamePlayer}</p>
      ) : data.length === 0 ? (
        <p className="text-warning">{t.progression.noData}</p>
      ) : (
        <ProgressionView
          data={data}
          joueur={nom}
          metricsDefault={METRIQUES_DEFAUT}
          defaultSelectedLabels={DEFAULT_SELECTED}
          tableCols={TABLE_COLS}
        />
      )}
    </div>
  );
}
