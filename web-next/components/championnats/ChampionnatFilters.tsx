"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { parseList } from "@/lib/filters";
import { unaccent } from "@/lib/format";
import { Icon } from "@/components/ui/Icon";
import type { Nationalite } from "@/lib/queries/referentiels";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { interpolate } from "@/lib/i18n/dictionaries";

// Nouveau critère de recherche (pas d'équivalent Streamlit) : nationalité,
// en complément des filtres globaux (Saison/Ligues/Postes/Âge/Minutes,
// désormais actifs sur cette page — cf. sidebar/Filters.tsx) qu'on ne
// duplique pas ici. Même convention de param que ligues/postes : absent =
// toutes, "__none__" = aucune, sinon liste CSV de codes. Rendu en liste
// déroulante (fermée par défaut, sélection faite dedans) plutôt qu'un
// panneau toujours ouvert sur la page.
export function ChampionnatFilters({
  nationalites,
  t,
}: {
  nationalites: Nationalite[];
  t: Dictionary;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  const allIds = nationalites.map((n) => n.nationalite_id);
  const selected = parseList(searchParams.get("nat") ?? undefined, allIds);

  function update(nat: string[]) {
    const params = new URLSearchParams(searchParams.toString());
    if (nat.length === allIds.length) params.delete("nat");
    else if (nat.length === 0) params.set("nat", "__none__");
    else params.set("nat", nat.join(","));
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  }

  function toggle(id: string) {
    update(selected.includes(id) ? selected.filter((v) => v !== id) : [...selected, id]);
  }

  const filtered = useMemo(() => {
    const q = unaccent(search.trim());
    if (!q) return nationalites;
    return nationalites.filter((n) => unaccent(n.nom_fr).includes(q));
  }, [nationalites, search]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const summary =
    selected.length === allIds.length
      ? t.championnats.all
      : selected.length === 0
        ? t.championnats.none
        : selected.length === 1
          ? nationalites.find((n) => n.nationalite_id === selected[0])?.nom_fr
          : interpolate(t.championnats.nSelected, { n: selected.length });

  return (
    <div className="mb-4 relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="w-full flex items-center justify-between gap-2 bg-card border border-border rounded-lg px-3 py-2 text-sm text-text hover:border-primary transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <Icon name="public" size={16} />
          {t.championnats.nationality}
          <span className="text-text-muted">— {summary}</span>
        </span>
        <Icon name={open ? "expand_less" : "expand_more"} size={18} color="#8A8A8A" />
      </button>

      {open && (
        <div className="absolute z-20 mt-1 w-full bg-card border border-border rounded-lg p-3 shadow-xl">
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              autoFocus
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t.championnats.searchCountry}
              className="flex-1 bg-bg border border-border rounded-lg px-3 py-1.5 text-sm text-text"
            />
            <button
              type="button"
              onClick={() => update(allIds)}
              className="text-xs border border-primary text-primary rounded-lg px-3 hover:bg-primary hover:text-black transition-colors"
            >
              {t.common.all}
            </button>
            <button
              type="button"
              onClick={() => update([])}
              className="text-xs border border-primary text-primary rounded-lg px-3 hover:bg-primary hover:text-black transition-colors"
            >
              {t.common.none}
            </button>
          </div>

          <div className="max-h-[220px] overflow-y-auto grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-3 gap-y-0.5">
            {filtered.length === 0 ? (
              <p className="text-text-muted text-sm col-span-3">{t.championnats.noCountryFound}</p>
            ) : (
              filtered.map((n) => (
                <label
                  key={n.nationalite_id}
                  className="flex items-center gap-1.5 text-[0.78rem] text-text py-0.5 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(n.nationalite_id)}
                    onChange={() => toggle(n.nationalite_id)}
                    className="accent-primary"
                  />
                  {n.nom_fr}
                </label>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
