import { getJoueurFiche, type JoueurFiche } from "@/lib/queries/joueurs";
import { SearchCombobox } from "@/components/ui/SearchCombobox";
import { ComparisonPanel } from "@/components/player/ComparisonPanel";
import { ComparisonStatsTable } from "@/components/player/ComparisonStatsTable";
import { Icon } from "@/components/ui/Icon";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary } from "@/lib/i18n/dictionaries";

// Portage 1:1 de web/pages/03_Comparaison.py
export default async function ComparaisonPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const t = getDictionary(await getLocale());
  const STATS_TABLEAU = [
    { label: "Score Pépite ★", col: "score_pepite_corrige" },
    { label: t.metrics.pct_goals_p90, col: "buts_p90" },
    { label: t.metrics.pct_xg_p90, col: "xg_p90" },
    { label: t.metrics.pct_assists_p90, col: "passes_dec_p90" },
    { label: t.metrics.pct_xag_p90, col: "xag_p90" },
    { label: t.metrics.pct_key_passes_p90, col: "key_passes_p90" },
    { label: t.metrics.pct_dribbles_p90, col: "dribbles_p90" },
    { label: t.metrics.pct_tackles_p90, col: "tackles_p90" },
    { label: t.metrics.pct_interceptions_p90, col: "interceptions_p90" },
    { label: t.metrics.pct_passes_pct, col: "passes_pct" },
    { label: t.progression.colMinutes, col: "minutes", integer: true },
    { label: t.progression.colMatches, col: "matchs_joues", integer: true },
  ];

  const sp = await searchParams;
  const getStr = (k: string) => (typeof sp[k] === "string" ? (sp[k] as string) : undefined);
  const idARaw = getStr("joueur_a");
  const saisonA = getStr("saison_a");
  const idBRaw = getStr("joueur_b");
  const saisonB = getStr("saison_b");

  let rowA: JoueurFiche | null = null;
  let rowB: JoueurFiche | null = null;
  if (idARaw && saisonA) rowA = await getJoueurFiche(Number(idARaw), saisonA);
  if (idBRaw && saisonB) rowB = await getJoueurFiche(Number(idBRaw), saisonB);

  const labelA = rowA ? `${rowA.nom_complet} — ${rowA.equipe} — ${saisonA}` : "";
  const labelB = rowB ? `${rowB.nom_complet} — ${rowB.equipe} — ${saisonB}` : "";

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-2 flex items-center gap-2">
        <Icon name="compare_arrows" size={28} />
        {t.comparison.title}
      </h1>
      <p className="text-text-muted text-sm mb-6">{t.comparison.subtitle}</p>

      <div className="grid grid-cols-1 lg:grid-cols-[5fr_1fr_5fr] gap-4 items-start">
        <div>
          <div className="text-primary font-bold flex items-center gap-1.5 mb-2.5">
            <Icon name="circle" size={14} />
            {t.comparison.playerA}
          </div>
          <SearchCombobox
            kind="joueurs"
            placeholder="Ex: Saka"
            defaultValue={labelA}
            idParam="joueur_a"
            saisonParam="saison_a"
          />
        </div>
        <div className="flex items-center justify-center text-text-muted text-2xl py-1 lg:pt-10">vs</div>
        <div>
          <div className="text-danger font-bold flex items-center gap-1.5 mb-2.5">
            <Icon name="circle" size={14} color="#E05252" />
            {t.comparison.playerB}
          </div>
          <SearchCombobox
            kind="joueurs"
            placeholder="Ex: Saka"
            defaultValue={labelB}
            idParam="joueur_b"
            saisonParam="saison_b"
          />
        </div>
      </div>

      {!idARaw || !idBRaw ? (
        <p className="text-text-muted mt-6">{t.comparison.selectBoth}</p>
      ) : !rowA || !rowB ? (
        <p className="text-warning mt-6">{t.common.insufficientData}</p>
      ) : (
        <>
          <hr className="border-border my-6" />
          <ComparisonPanel
            rowA={rowA}
            rowB={rowB}
            nameA={`${rowA.nom_court || t.comparison.playerA} — ${saisonA}`}
            nameB={`${rowB.nom_court || t.comparison.playerB} — ${saisonB}`}
            t={t}
          />

          <hr className="border-border my-6" />
          <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
            <Icon name="table_chart" size={18} />
            {t.comparison.detailedStats}
          </h4>
          <ComparisonStatsTable
            stats={STATS_TABLEAU}
            rowA={rowA}
            rowB={rowB}
            nameA={`${rowA.nom_court || t.comparison.playerA} — ${saisonA}`}
            nameB={`${rowB.nom_court || t.comparison.playerB} — ${saisonB}`}
            showBetter
            statLabel={t.comparison.stat}
          />
        </>
      )}
    </div>
  );
}
