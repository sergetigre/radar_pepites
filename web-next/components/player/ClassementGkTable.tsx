"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { ClassementGkRow } from "@/lib/queries/gardiens";
import { formatNumber } from "@/lib/format";

type Row = ClassementGkRow & { rang_dynamique: number };

const COLS: { key: keyof Row; label: string }[] = [
  { key: "rang_dynamique", label: "Rang" },
  { key: "player_name", label: "Gardien" },
  { key: "team_name", label: "Équipe" },
  { key: "ligue_id", label: "Ligue" },
  { key: "age_actuel", label: "Âge" },
  { key: "saves_p90", label: "Arrêts/90" },
  { key: "goals_prevented_ss", label: "Buts évités" },
  { key: "save_pct_fb", label: "% Arrêts" },
  { key: "clean_sheets_fb", label: "Clean sheets" },
  { key: "minutes_ss", label: "Minutes" },
];

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
export function ClassementGkTable({ data }: { data: ClassementGkRow[] }) {
  const router = useRouter();
  const [search, setSearch] = useState("");

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
        placeholder="🔍 Filtrer par nom..."
        className="w-full max-w-md bg-card border border-border rounded-lg px-3 py-2 text-sm text-white mb-4"
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
                className="border-b border-border/50 cursor-pointer hover:bg-white/5"
              >
                {COLS.map((c) => (
                  <td key={c.key} className="py-1.5 pr-4 tabular-nums">
                    {formatCell(row, c.key)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-text-muted text-xs">
        ℹ️ L&apos;âge est calculé par rapport à aujourd&apos;hui, pas à la saison affichée — à
        interpréter avec prudence pour les saisons passées.
      </p>
    </div>
  );
}
