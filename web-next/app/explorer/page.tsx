import { getLigues, getSaisons } from "@/lib/queries/referentiels";
import { getClassement } from "@/lib/queries/joueurs";
import { parseFilters } from "@/lib/filters";
import { ExplorerTable } from "@/components/player/ExplorerTable";
import { Icon } from "@/components/ui/Icon";

// Portage 1:1 de web/pages/01_Explorer.py
export default async function ExplorerPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const [ligues, saisons] = await Promise.all([getLigues(), getSaisons()]);
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
        Explorer
      </h1>

      {filtreLigues.length === 0 || postes.length === 0 ? (
        <p className="text-warning">Sélectionnez au moins une ligue et un poste dans les filtres.</p>
      ) : (
        <ExplorerContent
          saison={saison}
          ligues={filtreLigues}
          postes={postes}
          minMin={minMin}
          ageMax={ageMax}
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
}: {
  saison: string;
  ligues: string[];
  postes: string[];
  minMin: number;
  ageMax: number;
}) {
  const df = await getClassement(saison, ligues, postes, ageMax, minMin);

  if (df.length === 0) {
    return <p className="text-text-muted">Aucun joueur ne correspond aux filtres actuels.</p>;
  }

  return <ExplorerTable data={df} saison={saison} />;
}
