"use client";

import { useMemo, useState } from "react";
import { LineProgression, type Metric, type ProgressionRow } from "@/components/charts/LineProgression";
import { BarProgression } from "@/components/charts/BarProgression";
import { Icon } from "@/components/ui/Icon";
import { formatNumber } from "@/lib/format";

// highlight: true pour les colonnes de performance réelle (stats /90,
// score) — surlignées meilleure valeur en vert / pire en rouge atténué
// dans "Détail par saison". Saison/Minutes/Matchs restent neutres (pas des
// indicateurs de performance en soi).
type ColDef = { col: string; label: string; highlight?: boolean };

function formatCell(v: number | boolean | string | null): string {
  if (v == null) return "—";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : formatNumber(v);
  return String(v);
}

// Portage 1:1 de web/pages/04_Progression.py / 08_Progression_GK.py —
// multiselect saisons/métriques + radio courbe/barres, en état client local
// (pas dans l'URL), comme les widgets Streamlit équivalents (session_state
// éphémère, pas partageable par lien — cf. ComparisonPanel en Phase 4).
export function ProgressionView({
  data,
  joueur,
  metricsDefault,
  defaultSelectedLabels,
  tableCols,
  fbrefNotice = false,
}: {
  data: ProgressionRow[];
  joueur: string;
  metricsDefault: Metric[];
  defaultSelectedLabels: string[];
  tableCols: ColDef[];
  fbrefNotice?: boolean;
}) {
  const saisonsDispo = data.map((d) => d.saison_courte);
  const [saisonsSel, setSaisonsSel] = useState<Set<string>>(() => new Set(saisonsDispo));
  const [view, setView] = useState<"Courbe" | "Barres groupées">("Courbe");
  const [metricsSelLabels, setMetricsSelLabels] = useState<Set<string>>(
    () => new Set(defaultSelectedLabels)
  );

  const dfFiltre = data.filter((d) => saisonsSel.has(d.saison_courte));
  const metricsSel = metricsDefault.filter((m) => metricsSelLabels.has(m.label));

  // Meilleure/pire valeur par colonne parmi les saisons affichées — recalculé
  // à chaque changement de sélection de saisons. Pas de surlignage si une
  // seule valeur ou si toutes les valeurs sont égales (rien à distinguer).
  const bestWorst = useMemo(() => {
    const result: Record<string, { best: number; worst: number } | undefined> = {};
    for (const c of tableCols) {
      if (!c.highlight) continue;
      const vals = dfFiltre
        .map((r) => r[c.col])
        .filter((v): v is number => typeof v === "number" && Number.isFinite(v));
      if (vals.length < 2) continue;
      const best = Math.max(...vals);
      const worst = Math.min(...vals);
      if (best !== worst) result[c.col] = { best, worst };
    }
    return result;
  }, [dfFiltre, tableCols]);

  function toggleSaison(s: string) {
    setSaisonsSel((prev) => {
      const next = new Set(prev);
      if (next.has(s)) next.delete(s);
      else next.add(s);
      return next;
    });
  }

  function toggleMetric(label: string) {
    setMetricsSelLabels((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }

  return (
    <div>
      <div className="mb-4">
        <label className="block text-[0.8rem] text-text-nav mb-1.5">Saisons à afficher</label>
        <div className="flex flex-wrap gap-2">
          {saisonsDispo.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => toggleSaison(s)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                saisonsSel.has(s)
                  ? "border-primary bg-primary/20 text-primary"
                  : "border-border text-text-muted"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {dfFiltre.length === 0 ? (
        <p className="text-text-muted text-sm">Sélectionnez au moins une saison.</p>
      ) : (
        <>
          {fbrefNotice && !dfFiltre.some((d) => d.has_fbref_data) && (
            <p className="text-text-muted text-sm mb-3">
              ℹ️ % Arrêts et Clean sheets % non disponibles pour cette ligue (données fbref
              absentes).
            </p>
          )}

          <div className="mb-4 flex items-center gap-4 flex-wrap">
            <span className="text-[0.8rem] text-text-nav">Type de visualisation</span>
            {(["Courbe", "Barres groupées"] as const).map((v) => (
              <label key={v} className="flex items-center gap-1.5 text-sm text-white">
                <input
                  type="radio"
                  name="view"
                  checked={view === v}
                  onChange={() => setView(v)}
                  className="accent-primary"
                />
                {v}
              </label>
            ))}
          </div>

          <div className="mb-4">
            <label className="block text-[0.8rem] text-text-nav mb-1.5">Métriques</label>
            <div className="flex flex-wrap gap-2">
              {metricsDefault.map((m) => (
                <button
                  key={m.label}
                  type="button"
                  onClick={() => toggleMetric(m.label)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                    metricsSelLabels.has(m.label)
                      ? "border-primary bg-primary/20 text-primary"
                      : "border-border text-text-muted"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {view === "Courbe" ? (
            <LineProgression data={dfFiltre} joueur={joueur} metrics={metricsSel} />
          ) : (
            <BarProgression data={dfFiltre} joueur={joueur} cols={metricsSel.map((m) => m.col)} />
          )}

          <hr className="border-border my-6" />
          <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
            <Icon name="table_chart" size={18} />
            Détail par saison
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border">
                  {tableCols.map((c) => (
                    <th key={c.col} className="text-left py-2 pr-4 text-text-muted font-semibold">
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dfFiltre.map((row, i) => (
                  <tr key={i} className="border-b border-border/50">
                    {tableCols.map((c) => {
                      const v = row[c.col];
                      const bw = bestWorst[c.col];
                      const isBest = bw != null && v === bw.best;
                      const isWorst = bw != null && v === bw.worst;
                      return (
                        <td
                          key={c.col}
                          className={`py-1.5 pr-4 tabular-nums ${
                            isBest ? "stat-best" : isWorst ? "stat-worst" : ""
                          }`}
                        >
                          {formatCell(v)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
