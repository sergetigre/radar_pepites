import { getLigues, getSaisons } from "@/lib/queries/referentiels";
import { getClassementGk } from "@/lib/queries/gardiens";
import { parseFilters } from "@/lib/filters";
import { ClassementGkTable } from "@/components/player/ClassementGkTable";
import { Icon } from "@/components/ui/Icon";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary, type Dictionary } from "@/lib/i18n/dictionaries";

// Portage 1:1 de web/pages/05_Classement_GK.py
export default async function ClassementGkPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const t = getDictionary(await getLocale());
  const sp = await searchParams;
  const [ligues, saisons] = await Promise.all([getLigues(), getSaisons()]);
  const allLigueIds = ligues.map((l) => l.ligue_id);
  const { saison, ligues: filtreLigues, minMin } = parseFilters(sp, allLigueIds, saisons[0] ?? "");

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-5 flex items-center gap-2">
        <Icon name="sports_handball" size={28} />
        {t.classementGk.title}
      </h1>

      {filtreLigues.length === 0 ? (
        <p className="text-warning">{t.classementGk.selectLeague}</p>
      ) : (
        <ClassementGkContent saison={saison} ligues={filtreLigues} minMin={minMin} t={t} />
      )}
    </div>
  );
}

async function ClassementGkContent({
  saison,
  ligues,
  minMin,
  t,
}: {
  saison: string;
  ligues: string[];
  minMin: number;
  t: Dictionary;
}) {
  const df = await getClassementGk(saison, ligues, minMin);

  if (df.length === 0) {
    return <p className="text-text-muted">{t.classementGk.noGkMatch}</p>;
  }

  return <ClassementGkTable data={df} t={t} />;
}
