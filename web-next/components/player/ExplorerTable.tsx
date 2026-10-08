"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ScatterXgButs } from "@/components/charts/ScatterXgButs";
import type { ClassementRow } from "@/lib/queries/joueurs";
import { formatNumber } from "@/lib/format";

type Row = ClassementRow & { rang_dynamique: number };

// highlight: true pour les colonnes de performance réelle — meilleure
// valeur en vert / pire en rouge atténué, recalculé sur les lignes
// actuellement affichées (après recherche rapide) — même principe que
// "Détail par saison" (Progression).
const COLS: { key: keyof Row; label: string; highlight?: boolean }[] = [
  { key: "rang_dynamique", label: "Rang" },
  { key: "joueur", label: "Joueur" },
  { key: "equipe", label: "Équipe" },
  { key: "ligue", label: "Ligue" },
  { key: "poste_id", label: "Poste" },
  { key: "age", label: "Âge" },
  { key: "score_corrige", label: "Score ★", highlight: true },
  { key: "xg_p90", label: "xG/90", highlight: true },
  { key: "buts_p90", label: "Buts/90", highlight: true },
  { key: "minutes", label: "Minutes" },
];

function formatCell(row: Row, key: keyof Row): string {
  const v = row[key];
  if (v == null) return "—";
  if (key === "score_corrige" || key === "xg_p90" || key === "buts_p90") return formatNumber(v as number);
  return String(v);
}

function toCsvValue(v: unknown): string {
  if (v == null) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

// Portage 1:1 de web/pages/01_Explorer.py — recherche rapide, rang
// dynamique (recalculé sur score_corrige après filtre texte, pas
// rang_global qui est figé), export CSV, clic-ligne -> Radar Joueur.
export function ExplorerTable({ data, saison }: { data: ClassementRow[]; saison: string }) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState<"classement" | "graphiques">("classement");

  const filtered: Row[] = useMemo(() => {
    const base = search
      ? data.filter((r) => r.joueur.toLowerCase().includes(search.toLowerCase()))
      : data;
    const sorted = [...base].sort((a, b) => {
      if (a.score_corrige == null && b.score_corrige == null) return 0;
      if (a.score_corrige == null) return 1;
      if (b.score_corrige == null) return -1;
      return b.score_corrige - a.score_corrige;
    });
    return sorted.map((r, i) => ({ ...r, rang_dynamique: i + 1 }));
  }, [data, search]);

  const dfG = filtered.filter((r) => r.xg_p90 != null && r.buts_p90 != null);

  // Meilleure/pire valeur par colonne parmi les lignes affichées (après
  // recherche). Contrairement à Progression (peu de saisons, valeurs
  // rarement à égalité), Explorer liste des dizaines de joueurs dont
  // beaucoup partagent la même valeur plancher (ex. 0.00 but/90 pour tous
  // les défenseurs) — surligner une valeur partagée par 30 lignes n'aide
  // personne. On ne surligne donc que si l'extrême est unique (un seul
  // joueur l'atteint) ; sinon ce n'est pas vraiment "le/la pire", juste
  // une valeur courante.
  const bestWorst = useMemo(() => {
    const result: Partial<Record<keyof Row, { best?: number; worst?: number }>> = {};
    for (const c of COLS) {
      if (!c.highlight) continue;
      const vals = filtered
        .map((r) => r[c.key])
        .filter((v): v is number => typeof v === "number" && Number.isFinite(v));
      if (vals.length < 2) continue;
      const best = Math.max(...vals);
      const worst = Math.min(...vals);
      if (best === worst) continue;
      const entry: { best?: number; worst?: number } = {};
      if (vals.filter((v) => v === best).length === 1) entry.best = best;
      if (vals.filter((v) => v === worst).length === 1) entry.worst = worst;
      if (entry.best !== undefined || entry.worst !== undefined) result[c.key] = entry;
    }
    return result;
  }, [filtered]);

  function exportCsv() {
    const header = COLS.map((c) => c.label).join(",");
    const lines = filtered.map((row) => COLS.map((c) => toCsvValue(row[c.key])).join(","));
    const csv = [header, ...lines].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `radarpepites_classement_${saison}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function selectRow(row: Row) {
    router.push(`/radar-joueur?prefill=${encodeURIComponent(row.joueur)}`);
  }

  return (
    <div>
      <div className="flex gap-1 mb-4 border-b border-border">
        {(
          [
            ["classement", "📋 Classement"],
            ["graphiques", "📊 Graphiques"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === key ? "text-primary border-primary" : "text-text-muted border-transparent"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "classement" ? (
        <>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="🔍 Filtrer par nom de joueur..."
            className="w-full max-w-md bg-card border border-border rounded-lg px-3 py-2 text-sm text-white mb-4"
          />
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border">
                  {COLS.map((c) => (
                    <th key={c.key} className="text-left py-2 pr-4 text-text-muted font-semibold">
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr
                    key={row.joueur_id}
                    onClick={() => selectRow(row)}
                    className="border-b border-border/50 cursor-pointer hover:bg-white/5"
                  >
                    {COLS.map((c) => {
                      const v = row[c.key];
                      const bw = bestWorst[c.key];
                      const isBest = bw != null && v === bw.best;
                      const isWorst = bw != null && v === bw.worst;
                      return (
                        <td
                          key={c.key}
                          className={`py-1.5 pr-4 tabular-nums ${
                            isBest ? "stat-best" : isWorst ? "stat-worst" : ""
                          }`}
                        >
                          {formatCell(row, c.key)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button
            type="button"
            onClick={exportCsv}
            className="text-sm border border-primary text-primary rounded-lg px-4 py-2 hover:bg-primary hover:text-black transition-colors"
          >
            ⬇️ Exporter en CSV
          </button>
        </>
      ) : dfG.length > 0 ? (
        <ScatterXgButs data={dfG} />
      ) : (
        <p className="text-text-muted text-sm">Données insuffisantes pour le graphique.</p>
      )}
    </div>
  );
}
