import { getLigues, getSaisons } from "@/lib/queries/referentiels";
import { getClassement } from "@/lib/queries/joueurs";
import { parseFilters } from "@/lib/filters";
import { ExplorerTable } from "@/components/player/ExplorerTable";
import { Icon } from "@/components/ui/Icon";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary } from "@/lib/i18n/dictionaries";

// Portage 1:1 de web/pages/01_Explorer.py
export default async function ExplorerPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const [ligues, saisons, locale] = await Promise.all([getLigues(), getSaisons(), getLocale()]);
  const t = getDictionary(locale);
  const allLigueIds = ligues.map((l) => l.ligue_id);
  const { saison, ligues: filtreLigues, postes, minMin, ageMax } = parseFilters(
    sp,
    allLigueIds,
    saisons[0] ?? ""
  );

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-5 flex items-center gap-2">
        <Icon name="search" size={28} />
        {t.explorer.title}
      </h1>

      {filtreLigues.length === 0 || postes.length === 0 ? (
        <p className="text-warning">{t.dashboard.selectFilters}</p>
      ) : (
        <ExplorerContent
          saison={saison}
          ligues={filtreLigues}
          postes={postes}
          minMin={minMin}
          ageMax={ageMax}
          t={t}
        />
      )}
    </div>
  );
}

async function ExplorerContent({
  saison,
  ligues,
  postes,
  minMin,
  ageMax,
  t,
}: {
  saison: string;
  ligues: string[];
  postes: string[];
  minMin: number;
  ageMax: number;
  t: ReturnType<typeof getDictionary>;
}) {
  const df = await getClassement(saison, ligues, postes, ageMax, minMin);

  if (df.length === 0) {
    return <p className="text-text-muted">{t.explorer.noPlayersMatch}</p>;
  }

  return <ExplorerTable data={df} saison={saison} t={t} />;
}
