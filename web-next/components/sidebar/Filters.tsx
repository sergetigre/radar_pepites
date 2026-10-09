"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { FAMILLES_POSTES, ALL_POSTES, type Ligue } from "@/lib/constants/postes";
import { parseFilters } from "@/lib/filters";
import { useI18n } from "@/components/i18n/I18nProvider";

export { parseFilters } from "@/lib/filters";

// Panneau repliable via <details>/<summary> HTML natif, PAS un useState +
// bouton React : ce composant utilise useSearchParams() et doit donc rester
// enveloppé par un <Suspense> (cf. layout.tsx). Un useState contrôlant une
// hauteur/visibilité sur un ancêtre de la frontière Suspense empêchait
// systématiquement celle-ci de s'hydrater (contenu invisible, coincé dans
// le placeholder de streaming SSR), quelle que soit la façon dont le state
// était organisé. <details> est purement HTML/CSS, zéro JS, donc hors de
// cause — déjà utilisé sans souci ici même pour les groupes de Postes.
export function Filters({ ligues, saisons }: { ligues: Ligue[]; saisons: string[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { t } = useI18n();

  const allLigueIds = ligues.map((l) => l.ligue_id);
  const current = parseFilters(searchParams, allLigueIds, saisons[0] ?? "");

  function updateParams(patch: Partial<Record<string, string>>) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(patch)) {
      if (value === undefined) params.delete(key);
      else params.set(key, value);
    }
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  }

  function toggleListValue(key: "ligues" | "postes", allValues: string[], value: string) {
    const list = key === "ligues" ? current.ligues : current.postes;
    const next = list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
    updateParams({ [key]: next.length === allValues.length ? undefined : next.join(",") });
  }

  function setAll(key: "ligues" | "postes") {
    updateParams({ [key]: undefined });
  }

  function setNone(key: "ligues" | "postes") {
    updateParams({ [key]: "__none__" });
  }

  return (
    <div className="px-3 pb-4">
      <details className="filters-details">
        <summary className="flex items-center justify-between text-[0.65rem] font-bold uppercase tracking-[2px] text-text-muted pt-2 pb-2.5 pl-0.5 cursor-pointer hover:text-text-nav transition-colors list-none">
          <span>
            <span className="material-icons-outlined text-[16px] align-middle mr-1 text-primary">
              tune
            </span>
            {t.sidebar.filters}
          </span>
          <span className="material-icons-outlined text-[16px] chevron" aria-hidden>
            expand_more
          </span>
        </summary>

        <div className="pt-1">
          {/* Saison */}
          <div>
            <label className="block text-[0.8rem] text-text-nav mb-1">{t.sidebar.season}</label>
            <select
              value={current.saison}
              onChange={(e) => updateParams({ saison: e.target.value })}
              className="w-full bg-card border border-border rounded-lg px-2 py-1.5 text-sm text-text mb-3"
            >
              {saisons.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Ligues */}
          <div>
            <div className="text-[0.72rem] font-semibold text-text mt-3 mb-1.5">
              <span className="material-icons-outlined text-[15px] align-middle mr-1">public</span>
              {t.sidebar.leagues}
            </div>
            <div className="grid grid-cols-2 gap-2 mb-1.5">
              <button
                type="button"
                onClick={() => setAll("ligues")}
                className="text-xs border border-primary text-primary rounded-lg py-1 hover:bg-primary hover:text-black transition-colors"
              >
                {t.common.all}
              </button>
              <button
                type="button"
                onClick={() => setNone("ligues")}
                className="text-xs border border-primary text-primary rounded-lg py-1 hover:bg-primary hover:text-black transition-colors"
              >
                {t.common.none}
              </button>
            </div>
            {ligues.map((l) => (
              <label key={l.ligue_id} className="flex items-center gap-2 text-[0.78rem] text-text py-0.5">
                <input
                  type="checkbox"
                  checked={current.ligues.includes(l.ligue_id)}
                  onChange={() => toggleListValue("ligues", allLigueIds, l.ligue_id)}
                  className="accent-primary"
                />
                {l.nom_complet}
              </label>
            ))}
          </div>

          {/* Postes */}
          <div>
            <div className="text-[0.72rem] font-semibold text-text mt-3 mb-1.5">
              <span className="material-icons-outlined text-[15px] align-middle mr-1">person</span>
              {t.sidebar.positions}
            </div>
            <div className="grid grid-cols-2 gap-2 mb-1.5">
              <button
                type="button"
                onClick={() => setAll("postes")}
                className="text-xs border border-primary text-primary rounded-lg py-1 hover:bg-primary hover:text-black transition-colors"
              >
                {t.common.all}
              </button>
              <button
                type="button"
                onClick={() => setNone("postes")}
                className="text-xs border border-primary text-primary rounded-lg py-1 hover:bg-primary hover:text-black transition-colors"
              >
                {t.common.none}
              </button>
            </div>
            {Object.entries(FAMILLES_POSTES).map(([famille, codes]) => (
              <details key={famille} open className="mb-1">
                <summary className="text-[0.78rem] text-text-nav cursor-pointer py-1">
                  {t.postes.familles[famille as keyof typeof t.postes.familles] ?? famille}
                </summary>
                <div className="pl-2">
                  {Object.keys(codes).map((code) => (
                    <label key={code} className="flex items-center gap-2 text-[0.78rem] text-text py-0.5">
                      <input
                        type="checkbox"
                        checked={current.postes.includes(code)}
                        onChange={() => toggleListValue("postes", ALL_POSTES, code)}
                        className="accent-primary"
                      />
                      {t.postes.labels[code as keyof typeof t.postes.labels] ?? code}
                    </label>
                  ))}
                </div>
              </details>
            ))}
          </div>

        </div>
      </details>

      <div className="border-t border-border mt-4 mb-2" />
      <p className="text-[0.72rem] text-text-muted">
        RadarPépites v1.0 · 10 {t.sidebar.footer} · 3 {t.sidebar.footerSeasons}
      </p>
    </div>
  );
}
