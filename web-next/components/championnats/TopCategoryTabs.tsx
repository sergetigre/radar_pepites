"use client";

import { useState } from "react";
import Link from "next/link";
import type { ClassementRow } from "@/lib/queries/joueurs";

const CATEGORIES: { label: string; col: keyof ClassementRow; colLabel: string }[] = [
  { label: "⚽ Buteurs", col: "buts_p90", colLabel: "Buts/90" },
  { label: "🎯 Passeurs", col: "assists_p90", colLabel: "Assists/90" },
  { label: "🏃 Dribbleurs", col: "dribbles_p90", colLabel: "Dribbles/90" },
  { label: "🛡️ Défenseurs", col: "tackles_p90", colLabel: "Tacles/90" },
  { label: "🧠 Créateurs", col: "key_passes_p90", colLabel: "Passes clés/90" },
];

const MEDALS: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

// Portage 1:1 de la section "Top 5 par catégorie" de
// web/pages/09_Championnats.py (st.tabs + bar-row cliquables).
export function TopCategoryTabs({ data, saison }: { data: ClassementRow[]; saison: string }) {
  const [activeIdx, setActiveIdx] = useState(0);
  const active = CATEGORIES[activeIdx];

  const top5 = data
    .filter((r) => r[active.col] != null)
    .sort((a, b) => (b[active.col] as number) - (a[active.col] as number))
    .slice(0, 5);

  const valeurMax = top5.length > 0 ? Math.max(...(top5.map((r) => r[active.col] as number)), 1) : 1;

  return (
    <div>
      <div className="flex gap-1 mb-4 border-b border-border flex-wrap">
        {CATEGORIES.map((c, i) => (
          <button
            key={c.label}
            type="button"
            onClick={() => setActiveIdx(i)}
            className={`px-3 py-2 text-sm font-medium border-b-2 -mb-px whitespace-nowrap ${
              i === activeIdx ? "text-primary border-primary" : "text-text-muted border-transparent"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {top5.length === 0 ? (
        <p className="text-text-muted text-sm">Données insuffisantes.</p>
      ) : (
        <div>
          {top5.map((row, i) => {
            const rank = i + 1;
            const medal = MEDALS[rank] ?? `${rank}.`;
            const value = row[active.col] as number;
            const pct = Math.max(6, Math.round((value / valeurMax) * 100));
            return (
              <Link
                key={row.joueur_id}
                href={`/radar-joueur?joueur_id=${row.joueur_id}&saison=${saison}`}
                className="no-underline block"
              >
                <div className="bar-row">
                  <div className="min-w-[28px] text-center text-[0.9rem]">{medal}</div>
                  <div className="flex-none w-[200px] min-w-0">
                    <div className="font-bold text-white text-[0.85rem] whitespace-nowrap overflow-hidden text-ellipsis">
                      {row.joueur}
                    </div>
                    <div className="text-text-muted text-[0.7rem] whitespace-nowrap overflow-hidden text-ellipsis">
                      {row.equipe} · {row.poste_id}
                    </div>
                  </div>
                  <div className="flex-1 h-[10px] bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${pct}%`,
                        background: "linear-gradient(90deg,#2DAD7E,#5DCBA0)",
                      }}
                    />
                  </div>
                  <div className="min-w-[64px] text-right font-bold text-white text-[0.82rem] whitespace-nowrap">
                    {value.toFixed(2)}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
