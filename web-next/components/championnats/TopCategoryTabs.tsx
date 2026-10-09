"use client";

import { useState } from "react";
import Link from "next/link";
import type { ClassementRow } from "@/lib/queries/joueurs";
import { teamLogoUrl, ligueLogoUrl, ligueLogoInvert } from "@/lib/media";
import { useI18n } from "@/components/i18n/I18nProvider";

const MEDALS: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

// Portage 1:1 de la section "Top 5 par catégorie" de
// web/pages/09_Championnats.py (st.tabs + bar-row cliquables).
export function TopCategoryTabs({ data, saison }: { data: ClassementRow[]; saison: string }) {
  const { t } = useI18n();
  const CATEGORIES: { label: string; col: keyof ClassementRow }[] = [
    { label: `⚽ ${t.championnats.categoryScorers}`, col: "buts_p90" },
    { label: `🎯 ${t.championnats.categoryPlaymakers}`, col: "assists_p90" },
    { label: `🏃 ${t.championnats.categoryDribblers}`, col: "dribbles_p90" },
    { label: `🛡️ ${t.championnats.categoryDefenders}`, col: "tackles_p90" },
    { label: `🧠 ${t.championnats.categoryCreators}`, col: "key_passes_p90" },
  ];
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
        <p className="text-text-muted text-sm">{t.common.insufficientData}</p>
      ) : (
        <div>
          {top5.map((row, i) => {
            const rank = i + 1;
            const medal = MEDALS[rank] ?? `${rank}.`;
            const value = row[active.col] as number;
            const pct = Math.max(6, Math.round((value / valeurMax) * 100));
            const clubUrl = teamLogoUrl(row.team_id_ss);
            const ligueUrl = ligueLogoUrl(row.ligue_id);
            const posteLabel = row.poste_id
              ? t.postes.labels[row.poste_id as keyof typeof t.postes.labels] ?? row.poste_id
              : "";
            return (
              <Link
                key={row.joueur_id}
                href={`/radar-joueur?joueur_id=${row.joueur_id}&saison=${saison}`}
                className="no-underline block"
              >
                <div className="bar-row flex-wrap">
                  <div className="order-1 min-w-[28px] text-center text-[0.9rem]">{medal}</div>
                  <div className="order-2 flex-1 min-w-0 md:flex-none md:w-[220px]">
                    <div className="font-bold text-text text-[0.85rem] whitespace-nowrap overflow-hidden text-ellipsis">
                      {row.joueur}
                    </div>
                    <div className="flex items-center gap-1 text-text-muted text-[0.7rem]">
                      {clubUrl && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={clubUrl} alt="" className="club-logo" />
                      )}
                      <span className="whitespace-nowrap overflow-hidden text-ellipsis min-w-0">
                        {row.equipe} · {posteLabel}
                      </span>
                      {ligueUrl && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={ligueUrl}
                          alt=""
                          className={`ligue-logo${ligueLogoInvert(row.ligue_id) ? " ligue-logo-invert" : ""}`}
                        />
                      )}
                    </div>
                  </div>
                  <div className="order-3 md:order-4 min-w-[56px] shrink-0 text-right font-bold text-text text-[0.82rem] whitespace-nowrap">
                    {value.toFixed(2)}
                  </div>
                  <div className="order-4 md:order-3 basis-full md:basis-0 md:flex-1 h-[10px] bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${pct}%`,
                        background: "linear-gradient(90deg,#2DAD7E,#5DCBA0)",
                      }}
                    />
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
