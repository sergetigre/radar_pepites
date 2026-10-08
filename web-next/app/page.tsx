import { getLigues, getSaisons } from "@/lib/queries/referentiels";
import { getClassement } from "@/lib/queries/joueurs";
import { getKpis, topParLigue } from "@/lib/queries/dashboard";
import { parseFilters } from "@/lib/filters";
import { BarTop10 } from "@/components/charts/BarTop10";
import { ScatterXgButs } from "@/components/charts/ScatterXgButs";
import { KpiCard } from "@/components/ui/KpiCard";
import { PlayerMiniCard } from "@/components/ui/PlayerMiniCard";
import { formatNumber } from "@/lib/format";

// Portage 1:1 de web/pages/00_Tableau_de_bord.py
export default async function Home({
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
      <div className="py-2.5 pb-5">
        <h1 className="text-[1.8rem] font-extrabold m-0 flex items-center gap-2">
          <span className="material-icons-outlined text-[28px] text-primary">dashboard</span>
          Tableau de bord
        </h1>
        <p className="text-text-muted mt-1 text-sm">
          Saison {saison} · {filtreLigues.length} ligue(s) · {postes.length} poste(s)
        </p>
      </div>

      {filtreLigues.length === 0 || postes.length === 0 ? (
        <p className="text-warning">Sélectionnez au moins une ligue et un poste dans les filtres.</p>
      ) : (
        <DashboardContent
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

async function DashboardContent({
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
  const [kpis, df, dfLigue] = await Promise.all([
    getKpis(saison, ligues, postes, minMin, ageMax),
    getClassement(saison, ligues, postes, ageMax, minMin),
    topParLigue(saison, ligues, postes, minMin, ageMax),
  ]);

  const dfAtt = df.filter(
    (r) =>
      ["FW", "LW", "RW", "AM"].includes(r.poste_id) && r.xg_p90 != null && r.buts_p90 != null
  );

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiCard label="👥 Joueurs U23" value={kpis.nb.toLocaleString("en-US")} />
        <KpiCard label="🏆 Ligues" value={String(kpis.ligues)} />
        <KpiCard label="📊 Score moyen" value={formatNumber(kpis.moy)} />
        <KpiCard label="⭐ Meilleur score" value={formatNumber(kpis.max)} />
      </div>

      <div className="my-5" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <h4 className="text-[1.05rem] font-bold mb-2 flex items-center gap-1.5">
            <span className="material-icons-outlined text-[18px] text-primary">bar_chart</span>
            Top 10 Score Pépite
          </h4>
          {df.length > 0 ? (
            <BarTop10 data={df} />
          ) : (
            <p className="text-text-muted text-sm">Aucune donnée pour ces filtres.</p>
          )}
        </div>
        <div>
          <h4 className="text-[1.05rem] font-bold mb-2 flex items-center gap-1.5">
            <span className="material-icons-outlined text-[18px] text-primary">scatter_plot</span>
            xG vs Buts
          </h4>
          {dfAtt.length > 0 ? (
            <ScatterXgButs data={dfAtt} />
          ) : (
            <p className="text-text-muted text-sm">Aucune donnée pour ces filtres.</p>
          )}
        </div>
      </div>

      <hr className="border-border my-6" />
      <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
        <span className="material-icons-outlined text-[18px] text-primary">public</span>
        Meilleure pépite par ligue
      </h4>

      {dfLigue.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {dfLigue.map((row) => (
            <PlayerMiniCard key={row.ligue_id} row={row} saison={saison} />
          ))}
        </div>
      ) : (
        <p className="text-text-muted text-sm">Aucune donnée pour ces filtres.</p>
      )}
    </>
  );
}
