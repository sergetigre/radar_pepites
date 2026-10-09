"use client";

import { useState } from "react";
import Link from "next/link";
import type { ClassementRow } from "@/lib/queries/joueurs";
import type { TopGkScoreRow } from "@/lib/queries/gardiens";
import { teamLogoUrl, ligueLogoUrl, ligueLogoInvert } from "@/lib/media";
import { useI18n } from "@/components/i18n/I18nProvider";
import { interpolate } from "@/lib/i18n/dictionaries";
import { SafeImg } from "@/components/ui/SafeImg";

const MEDALS: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

type DisplayRow = {
  joueur_id: number;
  joueur: string;
  equipe: string;
  ligue_id: string | null;
  team_id_ss: number | null;
  posteLabel: string;
  value: number;
  urlBase: string;
};

// Portage 1:1 de la section "Top 5 par catégorie" de
// web/pages/09_Championnats.py (st.tabs + bar-row cliquables) — étendu
// avec un 6e onglet Gardiens (Arrêts/90, sourcé séparément car les GK ne
// sont pas dans `data`, filtrés par poste_id != 'GK' côté getClassement).
export function TopCategoryTabs({
  data,
  gkData,
  saison,
}: {
  data: ClassementRow[];
  gkData: TopGkScoreRow[];
  saison: string;
}) {
  const { t } = useI18n();
  const CATEGORIES = [
    {
      label: `⚽ ${t.championnats.categoryScorers}`,
      col: "buts_p90" as const,
      gk: false,
      statLabel: t.metricsShort.buts_p90,
    },
    {
      label: `🎯 ${t.championnats.categoryPlaymakers}`,
      col: "assists_p90" as const,
      gk: false,
      statLabel: t.metricsShort.passes_dec_p90,
    },
    {
      label: `🏃 ${t.championnats.categoryDribblers}`,
      col: "dribbles_p90" as const,
      gk: false,
      statLabel: t.metricsShort.dribbles_p90,
    },
    {
      label: `🛡️ ${t.championnats.categoryDefenders}`,
      col: "tackles_p90" as const,
      gk: false,
      statLabel: t.metricsShort.tackles_p90,
    },
    {
      label: `🧠 ${t.championnats.categoryCreators}`,
      col: "key_passes_p90" as const,
      gk: false,
      statLabel: t.metricsShort.key_passes_p90,
    },
    {
      label: `🧤 ${t.championnats.categoryGoalkeepers}`,
      col: "saves_p90" as const,
      gk: true,
      statLabel: t.metricsShort.saves_p90,
    },
  ];
  const [activeIdx, setActiveIdx] = useState(0);
  const active = CATEGORIES[activeIdx];

  const rows: DisplayRow[] = active.gk
    ? gkData
        .filter((r) => r.saves_p90 != null)
        .map((r) => ({
          joueur_id: r.joueur_id,
          joueur: r.joueur,
          equipe: r.equipe,
          ligue_id: r.ligue_id,
          team_id_ss: r.team_id_ss,
          posteLabel: t.postes.labels.GK,
          value: r.saves_p90 as number,
          urlBase: "/radar-gk",
        }))
    : data
        .filter((r) => r[active.col as keyof ClassementRow] != null)
        .map((r) => ({
          joueur_id: r.joueur_id,
          joueur: r.joueur,
          equipe: r.equipe,
          ligue_id: r.ligue_id,
          team_id_ss: r.team_id_ss,
          posteLabel: r.poste_id
            ? t.postes.labels[r.poste_id as keyof typeof t.postes.labels] ?? r.poste_id
            : "",
          value: r[active.col as keyof ClassementRow] as number,
          urlBase: "/radar-joueur",
        }));

  const top5 = [...rows].sort((a, b) => b.value - a.value).slice(0, 5);

  const valeurMax = top5.length > 0 ? Math.max(...top5.map((r) => r.value), 1) : 1;

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

      <p className="text-text-muted text-[0.72rem] uppercase tracking-wide mb-2">
        {interpolate(t.championnats.rankedBy, { metric: active.statLabel })}
      </p>

      {top5.length === 0 ? (
        <p className="text-text-muted text-sm">{t.common.insufficientData}</p>
      ) : (
        <div>
          {top5.map((row, i) => {
            const rank = i + 1;
            const medal = MEDALS[rank] ?? `${rank}.`;
            const pct = Math.max(6, Math.round((row.value / valeurMax) * 100));
            const clubUrl = teamLogoUrl(row.team_id_ss);
            const ligueUrl = ligueLogoUrl(row.ligue_id);
            return (
              <Link
                key={row.joueur_id}
                href={`${row.urlBase}?joueur_id=${row.joueur_id}&saison=${saison}`}
                className="no-underline block"
              >
                <div className="bar-row flex-wrap">
                  <div className="order-1 min-w-[28px] text-center text-[0.9rem]">{medal}</div>
                  <div className="order-2 flex-1 min-w-0 md:flex-none md:w-[220px]">
                    <div className="font-bold text-text text-[0.85rem] whitespace-nowrap overflow-hidden text-ellipsis">
                      {row.joueur}
                    </div>
                    <div className="flex items-center gap-1 text-text-muted text-[0.7rem]">
                      <SafeImg src={clubUrl} className="club-logo" />
                      <span className="whitespace-nowrap overflow-hidden text-ellipsis min-w-0">
                        {row.equipe} · {row.posteLabel}
                      </span>
                      <SafeImg
                        src={ligueUrl}
                        className={`ligue-logo${ligueLogoInvert(row.ligue_id) ? " ligue-logo-invert" : ""}`}
                      />
                    </div>
                  </div>
                  <div className="order-3 md:order-4 min-w-[56px] shrink-0 text-right font-bold text-text text-[0.82rem] whitespace-nowrap">
                    {row.value.toFixed(2)}
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
