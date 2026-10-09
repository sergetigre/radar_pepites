"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { ClassementGkRow } from "@/lib/queries/gardiens";
import { formatNumber } from "@/lib/format";
import { teamLogoUrl, ligueLogoUrl, ligueLogoInvert } from "@/lib/media";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { SafeImg } from "@/components/ui/SafeImg";

type Row = ClassementGkRow & { rang_dynamique: number };

function buildCols(t: Dictionary): { key: keyof Row; label: string }[] {
  return [
    { key: "rang_dynamique", label: t.explorer.colRank },
    { key: "player_name", label: t.classementGk.colGk },
    { key: "team_name", label: t.explorer.colTeam },
    { key: "ligue_id", label: t.explorer.colLeague },
    { key: "age_actuel", label: t.explorer.colAge },
    { key: "saves_p90", label: t.metricsShort.saves_p90 },
    { key: "goals_prevented_ss", label: t.metricsShort.goals_prevented },
    { key: "save_pct_fb", label: t.metrics.pct_save_pct },
    { key: "clean_sheets_fb", label: t.metrics.pct_clean_sheets_pct },
    { key: "minutes_ss", label: t.explorer.colMinutes },
  ];
}

function formatCell(row: Row, key: keyof Row): string {
  const v = row[key];
  if (v == null) return "—";
  if (key === "saves_p90" || key === "goals_prevented_ss" || key === "save_pct_fb") {
    return formatNumber(v as number);
  }
  return String(v);
}

// Portage 1:1 de web/pages/05_Classement_GK.py — pas d'export CSV ni
// d'onglet Graphiques ici (asymétrie volontaire avec Explorer, présente
// dans le code source). Classement_id affiché brut (ex. "ENG"), pas le nom
// complet de ligue — autre écart assumé avec Explorer, fidèle à l'original.
export function ClassementGkTable({ data, t }: { data: ClassementGkRow[]; t: Dictionary }) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const COLS = useMemo(() => buildCols(t), [t]);

  const filtered: Row[] = useMemo(() => {
    const base = search
      ? data.filter((r) => r.player_name.toLowerCase().includes(search.toLowerCase()))
      : data;
    const sorted = [...base].sort((a, b) => {
      if (a.saves_p90 == null && b.saves_p90 == null) return 0;
      if (a.saves_p90 == null) return 1;
      if (b.saves_p90 == null) return -1;
      return b.saves_p90 - a.saves_p90;
    });
    return sorted.map((r, i) => ({ ...r, rang_dynamique: i + 1 }));
  }, [data, search]);

  function selectRow(row: Row) {
    router.push(`/radar-gk?prefill=${encodeURIComponent(row.player_name)}`);
  }

  return (
    <div>
      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder={`🔍 ${t.classementGk.searchPlaceholder}`}
        className="w-full max-w-md bg-card border border-border rounded-lg px-3 py-2 text-sm text-text mb-4"
      />
      <div className="overflow-x-auto mb-3">
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
                key={row.player_id_ss}
                onClick={() => selectRow(row)}
                className="border-b border-border/50 cursor-pointer hover:bg-overlay"
              >
                {COLS.map((c) => (
                  <td key={c.key} className="py-1.5 pr-4 tabular-nums">
                    {c.key === "team_name" ? (
                      <span className="flex items-center gap-1 whitespace-nowrap">
                        <SafeImg src={teamLogoUrl(row.team_id_ss)} className="club-logo" />
                        {row.team_name}
                      </span>
                    ) : c.key === "ligue_id" ? (
                      <span className="flex items-center gap-1 whitespace-nowrap">
                        <SafeImg
                          src={ligueLogoUrl(row.ligue_id)}
                          className={`ligue-logo${
                            ligueLogoInvert(row.ligue_id) ? " ligue-logo-invert" : ""
                          }`}
                        />
                        {row.ligue_id}
                      </span>
                    ) : (
                      formatCell(row, c.key)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-text-muted text-xs">ℹ️ {t.classementGk.ageDisclaimer}</p>
    </div>
  );
}
