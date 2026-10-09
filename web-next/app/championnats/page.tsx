import { getLigues, getSaisons, getNationalites } from "@/lib/queries/referentiels";
import { getClassement } from "@/lib/queries/joueurs";
import { getTopGkScore } from "@/lib/queries/gardiens";
import { parseFilters, parseList, getParam } from "@/lib/filters";
import { ChampionnatFilters } from "@/components/championnats/ChampionnatFilters";
import { TopCategoryTabs } from "@/components/championnats/TopCategoryTabs";
import { OnzeType } from "@/components/championnats/OnzeType";
import { PepitesSousCotees } from "@/components/championnats/PepitesSousCotees";
import { Icon } from "@/components/ui/Icon";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary, interpolate, type Dictionary } from "@/lib/i18n/dictionaries";

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
  const t = getDictionary(await getLocale());
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
        {t.championnats.title}
      </h1>
      <p className="text-text-muted text-sm mb-1">{t.championnats.subtitle}</p>
      <p className="text-text-muted text-sm mb-5">
        {interpolate(t.championnats.subtitleCounts, {
          season: saison,
          leagues: selLigues.length,
          nationalities: selNationalites.length,
        })}
      </p>

      <ChampionnatFilters nationalites={nationalites} t={t} />

      {selLigues.length === 0 || postes.length === 0 || selNationalites.length === 0 ? (
        <p className="text-warning">{t.championnats.selectFilters}</p>
      ) : (
        <ChampionnatContent
          saison={saison}
          ligues={selLigues}
          postes={postes}
          nationalites={selNationalites}
          minMin={minMin}
          ageMax={ageMax}
          t={t}
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
  t,
}: {
  saison: string;
  ligues: string[];
  postes: string[];
  nationalites: string[];
  minMin: number;
  ageMax: number;
  t: Dictionary;
}) {
  const [classement, gkTop] = await Promise.all([
    getClassement(saison, ligues, postes.length > 0 ? postes : POSTES_ORDER, ageMax, minMin),
    getTopGkScore(saison, ligues, minMin, ageMax, 3, nationalites),
  ]);
  const data = classement.filter((r) => nationalites.includes(r.nationalite_principale ?? ""));

  if (data.length === 0) {
    return <p className="text-text-muted mt-4">{t.championnats.noData}</p>;
  }

  return (
    <>
      <hr className="border-border my-6" />
      <h3 className="text-[1.15rem] font-bold mb-1 flex items-center gap-1.5">
        <Icon name="leaderboard" size={20} />
        {t.championnats.top5Title}
      </h3>
      <p className="text-text-muted text-sm mb-4">{t.championnats.top5Subtitle}</p>
      <TopCategoryTabs data={data} saison={saison} />

      <hr className="border-border my-6" />
      <h3 className="text-[1.15rem] font-bold mb-1 flex items-center gap-1.5">
        <Icon name="sports_soccer" size={20} />
        {t.championnats.onzeTypeTitle}
      </h3>
      <p className="text-text-muted text-sm mb-2">{t.championnats.onzeTypeSubtitle}</p>
      <OnzeType data={data} gkTop={gkTop} saison={saison} />

      <hr className="border-border my-6" />
      <h3 className="text-[1.15rem] font-bold mb-1 flex items-center gap-1.5">
        <Icon name="diamond" size={20} />
        {t.championnats.pepitesTitle}
      </h3>
      <p className="text-text-muted text-sm mb-4">{t.championnats.pepitesSubtitle}</p>
      <PepitesSousCotees data={data} saison={saison} />
    </>
  );
}
