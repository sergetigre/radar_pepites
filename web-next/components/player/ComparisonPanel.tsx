"use client";

import { useState } from "react";
import { RadarCompare } from "@/components/charts/RadarCompare";
import { ALL_STATS_COMPARE, ALL_STATS_COMPARE_KEYS, ALL_STATS_COMPARE_ICONS } from "@/lib/charts-config";
import { Icon } from "@/components/ui/Icon";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { interpolate } from "@/lib/i18n/dictionaries";

const FLAT_STATS = ALL_STATS_COMPARE_KEYS.flatMap((k) => ALL_STATS_COMPARE[k]);
const MIN_SEL = 4;
const MAX_SEL = 8;

// Portage de web/utils/components.py::stat_checkbox_selector() +
// web/pages/03_Comparaison.py (sélection 4-8 stats -> radar_compare).
export function ComparisonPanel({
  rowA,
  rowB,
  nameA,
  nameB,
  t,
}: {
  rowA: Record<string, unknown>;
  rowB: Record<string, unknown>;
  nameA: string;
  nameB: string;
  t: Dictionary;
}) {
  const [selected, setSelected] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    FLAT_STATS.forEach((s, i) => {
      init[s] = i < MIN_SEL;
    });
    return init;
  });

  const total = FLAT_STATS.filter((s) => selected[s]).length;
  const axesSel = FLAT_STATS.filter((s) => selected[s]);

  function toggle(stat: string, checked: boolean) {
    if (!checked && total >= MAX_SEL) return; // désactivé, comme côté Streamlit
    setSelected((prev) => ({ ...prev, [stat]: !checked }));
  }

  return (
    <div>
      <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
        <Icon name="tune" size={18} />
        {t.comparison.chooseStats}
      </h4>

      <details open className="mb-4">
        <summary className="text-[0.85rem] text-text-nav cursor-pointer py-1 mb-2">
          {t.comparison.selectStats}
        </summary>
        {ALL_STATS_COMPARE_KEYS.map((cat) => (
          <div key={cat}>
            <div className="text-[0.7rem] font-bold uppercase tracking-[1.5px] text-text-muted mt-2.5 mb-1.5">
              {ALL_STATS_COMPARE_ICONS[cat]} {t.radar[cat]}
            </div>
            {ALL_STATS_COMPARE[cat].map((s) => {
              const checked = !!selected[s];
              const disabled = !checked && total >= MAX_SEL;
              return (
                <label
                  key={s}
                  className={`flex items-center gap-2 text-[0.85rem] text-text py-0.5 ${
                    disabled ? "opacity-50" : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => toggle(s, checked)}
                    className="accent-primary"
                  />
                  {t.metrics[s as keyof typeof t.metrics] ?? s}
                </label>
              );
            })}
          </div>
        ))}
        <div className="mt-2 text-right">
          <span className={`stat-counter ${total >= MAX_SEL ? "full" : ""}`}>
            {total}/{MAX_SEL} {t.comparison.statsSuffix}
          </span>
        </div>
      </details>

      {total < MIN_SEL ? (
        <p className="text-warning text-sm">
          {interpolate(t.comparison.selectAtLeast, { n: MIN_SEL })}
        </p>
      ) : (
        <>
          <h4 className="text-[1.05rem] font-bold mb-3 flex items-center gap-1.5">
            <Icon name="radar" size={18} />
            {t.comparison.radarComparison}
          </h4>
          <RadarCompare rowA={rowA} rowB={rowB} axes={axesSel} nameA={nameA} nameB={nameB} labels={t.metrics} />
        </>
      )}
    </div>
  );
}
