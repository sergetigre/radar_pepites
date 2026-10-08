"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

type SearchResult = { joueur_id: number; saison_id?: string; joueur?: string; joueur_saison?: string };

// Équivalent de web/utils/search.py (streamlit-searchbox) : suggestions
// live dès 2 caractères, debounce, sélection → navigation vers la fiche.
// idParam/saisonParam permettent d'avoir deux combobox indépendants sur une
// même page (Comparaison : joueur_a/saison_a et joueur_b/saison_b) sans que
// l'un écrase la sélection de l'autre dans l'URL.
// `unique` bascule vers search_joueurs_unique()/search_gk_unique() (un
// résultat par joueur toutes saisons confondues, utilisé par Progression) —
// pas de saisonParam écrit dans ce mode, l'URL ne porte que l'id joueur.
export function SearchCombobox({
  kind,
  placeholder,
  defaultValue = "",
  idParam = "joueur_id",
  saisonParam = "saison",
  unique = false,
}: {
  kind: "joueurs" | "gardiens";
  placeholder: string;
  defaultValue?: string;
  idParam?: string;
  saisonParam?: string;
  unique?: boolean;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [term, setTerm] = useState(defaultValue);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const endpoint = unique ? `${kind}-unique` : kind;

  useEffect(() => {
    if (term.trim().length < 2) {
      setResults([]);
      return;
    }
    // AbortController plutôt qu'un simple clearTimeout : le debounce évite
    // de lancer une requête par frappe, mais une fois une requête partie,
    // rien n'empêchait une réponse pour un terme plus ancien ("Sak") de
    // revenir APRÈS celle du terme le plus récent ("Saka") et d'écraser les
    // bons résultats avec des résultats périmés — d'où le blocage observé
    // en tapant vite. L'abort annule la requête précédente dès que `term`
    // change, garantissant qu'une seule réponse peut jamais être appliquée.
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search/${endpoint}?q=${encodeURIComponent(term)}`, {
          signal: controller.signal,
        });
        const data: SearchResult[] = await res.json();
        setResults(data);
        setOpen(true);
      } catch (err) {
        if ((err as Error).name !== "AbortError") throw err;
      }
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [term, endpoint]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function select(r: SearchResult) {
    setTerm((unique ? r.joueur : r.joueur_saison) ?? "");
    setOpen(false);
    const params = new URLSearchParams(searchParams.toString());
    params.set(idParam, String(r.joueur_id));
    if (!unique && r.saison_id) params.set(saisonParam, r.saison_id);
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <div ref={containerRef} className="relative max-w-md">
      <input
        type="text"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder={placeholder}
        className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-white"
      />
      {open && results.length > 0 && (
        <div className="absolute z-10 mt-1 w-full bg-card border border-border rounded-lg max-h-72 overflow-y-auto">
          {results.map((r) => (
            <button
              key={`${r.joueur_id}-${r.saison_id ?? ""}`}
              type="button"
              onClick={() => select(r)}
              className="block w-full text-left px-3 py-2 text-sm text-white hover:bg-white/5"
            >
              {unique ? r.joueur : r.joueur_saison}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
