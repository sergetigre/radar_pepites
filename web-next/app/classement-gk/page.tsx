import { getLigues, getSaisons } from "@/lib/queries/referentiels";
import { getClassementGk } from "@/lib/queries/gardiens";
import { parseFilters } from "@/lib/filters";
import { ClassementGkTable } from "@/components/player/ClassementGkTable";
import { Icon } from "@/components/ui/Icon";

// Portage 1:1 de web/pages/05_Classement_GK.py
export default async function ClassementGkPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const [ligues, saisons] = await Promise.all([getLigues(), getSaisons()]);
  const allLigueIds = ligues.map((l) => l.ligue_id);
  const { saison, ligues: filtreLigues, minMin } = parseFilters(sp, allLigueIds, saisons[0] ?? "");

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-5 flex items-center gap-2">
        <Icon name="sports_handball" size={28} />
        Classement Gardiens
      </h1>

      {filtreLigues.length === 0 ? (
        <p className="text-warning">Sélectionnez au moins une ligue dans les filtres.</p>
      ) : (
        <ClassementGkContent saison={saison} ligues={filtreLigues} minMin={minMin} />
      )}
    </div>
  );
}

async function ClassementGkContent({
  saison,
  ligues,
  minMin,
}: {
  saison: string;
  ligues: string[];
  minMin: number;
}) {
  const df = await getClassementGk(saison, ligues, minMin);

  if (df.length === 0) {
    return <p className="text-text-muted">Aucun gardien ne correspond aux filtres actuels.</p>;
  }

  return <ClassementGkTable data={df} />;
}
