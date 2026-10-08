"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { FAMILLES_POSTES, ALL_POSTES, type Ligue } from "@/lib/constants/postes";
import { MINUTES_OPTIONS, parseFilters } from "@/lib/filters";

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

  const allLigueIds = ligues.map((l) => l.ligue_id);
  const current = parseFilters(searchParams, allLigueIds, saisons[0] ?? "");

  // État local pour les deux sliders : l'affichage suit la souris en temps
  // réel, mais la navigation (router.push -> refetch serveur) ne se
  // déclenche qu'au relâchement. Sans ça, onChange d'un <input type=range>
  // contrôlé par React se déclenche à CHAQUE pixel de glissement, donc
  // chaque micro-mouvement relançait une requête serveur complète — le
  // curseur devenait saccadé et quasi impossible à régler précisément.
  const minMinIdxFromUrl = (() => {
    const idx = MINUTES_OPTIONS.indexOf(current.minMin);
    return idx === -1 ? 3 : idx;
  })();
  const [minMinIdx, setMinMinIdx] = useState(minMinIdxFromUrl);
  const [ageMax, setAgeMax] = useState(current.ageMax);

  useEffect(() => setMinMinIdx(minMinIdxFromUrl), [minMinIdxFromUrl]);
  useEffect(() => setAgeMax(current.ageMax), [current.ageMax]);

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
            Filtres
          </span>
          <span className="material-icons-outlined text-[16px] chevron" aria-hidden>
            expand_more
          </span>
        </summary>

        <div className="pt-1">
          {/* Saison */}
          <div>
            <label className="block text-[0.8rem] text-text-nav mb-1">Saison</label>
            <select
              value={current.saison}
              onChange={(e) => updateParams({ saison: e.target.value })}
              className="w-full bg-card border border-border rounded-lg px-2 py-1.5 text-sm text-white mb-3"
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
            <div className="text-[0.72rem] font-semibold text-white mt-3 mb-1.5">
              <span className="material-icons-outlined text-[15px] align-middle mr-1">public</span>
              Ligues
            </div>
            <div className="grid grid-cols-2 gap-2 mb-1.5">
              <button
                type="button"
                onClick={() => setAll("ligues")}
                className="text-xs border border-primary text-primary rounded-lg py-1 hover:bg-primary hover:text-black transition-colors"
              >
                Tout
              </button>
              <button
                type="button"
                onClick={() => setNone("ligues")}
                className="text-xs border border-primary text-primary rounded-lg py-1 hover:bg-primary hover:text-black transition-colors"
              >
                Aucun
              </button>
            </div>
            {ligues.map((l) => (
              <label key={l.ligue_id} className="flex items-center gap-2 text-[0.78rem] text-white py-0.5">
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
            <div className="text-[0.72rem] font-semibold text-white mt-3 mb-1.5">
              <span className="material-icons-outlined text-[15px] align-middle mr-1">person</span>
              Postes
            </div>
            <div className="grid grid-cols-2 gap-2 mb-1.5">
              <button
                type="button"
                onClick={() => setAll("postes")}
                className="text-xs border border-primary text-primary rounded-lg py-1 hover:bg-primary hover:text-black transition-colors"
              >
                Tout
              </button>
              <button
                type="button"
                onClick={() => setNone("postes")}
                className="text-xs border border-primary text-primary rounded-lg py-1 hover:bg-primary hover:text-black transition-colors"
              >
                Aucun
              </button>
            </div>
            {Object.entries(FAMILLES_POSTES).map(([famille, codes]) => (
              <details key={famille} open className="mb-1">
                <summary className="text-[0.78rem] text-text-nav cursor-pointer py-1">
                  {famille}
                </summary>
                <div className="pl-2">
                  {Object.entries(codes).map(([code, label]) => (
                    <label key={code} className="flex items-center gap-2 text-[0.78rem] text-white py-0.5">
                      <input
                        type="checkbox"
                        checked={current.postes.includes(code)}
                        onChange={() => toggleListValue("postes", ALL_POSTES, code)}
                        className="accent-primary"
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </details>
            ))}
          </div>

          {/* Minutes min */}
          <label className="block text-[0.8rem] text-white mt-3 mb-1">
            ⏱️ Minutes min : {MINUTES_OPTIONS[minMinIdx]}
          </label>
          <input
            type="range"
            min={0}
            max={MINUTES_OPTIONS.length - 1}
            step={1}
            value={minMinIdx}
            onChange={(e) => setMinMinIdx(Number(e.target.value))}
            onMouseUp={(e) =>
              updateParams({ min_min: String(MINUTES_OPTIONS[Number(e.currentTarget.value)]) })
            }
            onTouchEnd={(e) =>
              updateParams({ min_min: String(MINUTES_OPTIONS[Number(e.currentTarget.value)]) })
            }
            onKeyUp={(e) =>
              updateParams({ min_min: String(MINUTES_OPTIONS[Number(e.currentTarget.value)]) })
            }
            className="w-full accent-primary"
          />

          {/* Âge max */}
          <label className="block text-[0.8rem] text-white mt-3 mb-1">🎂 Âge max : {ageMax}</label>
          <input
            type="range"
            min={16}
            max={23}
            step={1}
            value={ageMax}
            onChange={(e) => setAgeMax(Number(e.target.value))}
            onMouseUp={(e) => updateParams({ age_max: e.currentTarget.value })}
            onTouchEnd={(e) => updateParams({ age_max: e.currentTarget.value })}
            onKeyUp={(e) => updateParams({ age_max: e.currentTarget.value })}
            className="w-full accent-primary"
          />
        </div>
      </details>

      <div className="border-t border-border mt-4 mb-2" />
      <p className="text-[0.72rem] text-text-muted">RadarPépites v1.0 · 10 ligues · 3 saisons</p>
    </div>
  );
}
