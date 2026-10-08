import { getLigues, getSaisons, getNationalites } from "@/lib/queries/referentiels";
import { getClassement } from "@/lib/queries/joueurs";
import { getTopGkScore } from "@/lib/queries/gardiens";
import { parseFilters, parseList, getParam } from "@/lib/filters";
import { ChampionnatFilters } from "@/components/championnats/ChampionnatFilters";
import { TopCategoryTabs } from "@/components/championnats/TopCategoryTabs";
import { OnzeType } from "@/components/championnats/OnzeType";
import { PepitesSousCotees } from "@/components/championnats/PepitesSousCotees";
import { Icon } from "@/components/ui/Icon";

// DM (Milieu défensif) volontairement absent — cf. commentaire dans
// components/championnats/OnzeType.tsx.
const POSTES_ORDER = ["FW", "LW", "RW", "AM", "CM", "CB", "LB", "RB"];

// Page élargie à plusieurs championnats à la fois (au lieu d'un seul) + un
// nouveau critère Nationalité : objectif recruteur, pouvoir composer un
// "onze type" au-delà d'une seule ligue. Réutilise les filtres globaux de
// la sidebar (Saison/Ligues/Postes/Âge/Minutes, désormais actifs sur cette
// page — cf. sidebar/Filters.tsx) plutôt que de dupliquer des sélecteurs
// dédiés comme l'ancienne version (ChampionnatSelectors, supprimé).
export default async function ChampionnatsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const [ligues, saisons, nationalites] = await Promise.all([
    getLigues(),
    getSaisons(),
    getNationalites(),
  ]);
  const allLigueIds = ligues.map((l) => l.ligue_id);
  const allNatIds = nationalites.map((n) => n.nationalite_id);

  const { saison, ligues: selLigues, postes, minMin, ageMax } = parseFilters(
    sp,
    allLigueIds,
    saisons[0] ?? ""
  );
  const selNationalites = parseList(getParam(sp, "nat"), allNatIds);

  return (
    <div>
      <h1 className="text-[1.8rem] font-extrabold mb-1 flex items-center gap-2">
        <Icon name="emoji_events" size={28} />
        Top pépites
      </h1>
      <p className="text-text-muted text-sm mb-1">
        Classements, onze type et pépites sous-cotées — sur une ou plusieurs ligues, filtrables par
        nationalité pour cibler une recherche de recrutement.
      </p>
      <p className="text-text-muted text-sm mb-5">
        Saison {saison} · {selLigues.length} ligue(s) · {selNationalites.length} nationalité(s)
      </p>

      <ChampionnatFilters nationalites={nationalites} />

      {selLigues.length === 0 || postes.length === 0 || selNationalites.length === 0 ? (
        <p className="text-warning">
          Sélectionnez au moins une ligue, un poste (filtres) et une nationalité.
        </p>
      ) : (
        <ChampionnatContent
          saison={saison}
          ligues={selLigues}
          postes={postes}
          nationalites={selNationalites}
          minMin={minMin}
          ageMax={ageMax}
        />
      )}
    </div>
  );
}

async function ChampionnatContent({
  saison,
  ligues,
  postes,
  nationalites,
  minMin,
  ageMax,
}: {
  saison: string;
  ligues: string[];
  postes: string[];
  nationalites: string[];
  minMin: number;
  ageMax: number;
}) {
  const [classement, gkTop] = await Promise.all([
    getClassement(saison, ligues, postes.length > 0 ? postes : POSTES_ORDER, ageMax, minMin),
    getTopGkScore(saison, ligues, minMin, ageMax, 3, nationalites),
  ]);
  const data = classement.filter((r) => nationalites.includes(r.nationalite_principale ?? ""));

  if (data.length === 0) {
    return <p className="text-text-muted mt-4">Aucune donnée avec les filtres actuels.</p>;
  }

  return (
    <>
      <hr className="border-border my-6" />
      <h3 className="text-[1.15rem] font-bold mb-1 flex items-center gap-1.5">
        <Icon name="leaderboard" size={20} />
        Top 5 par catégorie
      </h3>
      <p className="text-text-muted text-sm mb-4">
        Les 5 joueurs les plus performants sur chaque qualité, parmi la sélection filtrée.
      </p>
      <TopCategoryTabs data={data} saison={saison} />

      <hr className="border-border my-6" />
      <h3 className="text-[1.15rem] font-bold mb-1 flex items-center gap-1.5">
        <Icon name="sports_soccer" size={20} />
        Onze type proposé
      </h3>
      <p className="text-text-muted text-sm mb-2">
        Titulaire (équipe, âge, note) + doublures juste en dessous, par poste — toutes ligues et
        nationalités sélectionnées confondues.
      </p>
      <OnzeType data={data} gkTop={gkTop} saison={saison} />

      <hr className="border-border my-6" />
      <h3 className="text-[1.15rem] font-bold mb-1 flex items-center gap-1.5">
        <Icon name="diamond" size={20} />
        Pépites sous-cotées
      </h3>
      <p className="text-text-muted text-sm mb-4">
        Score Pépite élevé (top 20% de la sélection) mais temps de jeu encore en dessous de la
        médiane — potentiel pas encore pleinement exploité.
      </p>
      <PepitesSousCotees data={data} saison={saison} />
    </>
  );
}
