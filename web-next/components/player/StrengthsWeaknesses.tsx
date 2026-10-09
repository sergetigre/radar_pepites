import { Icon } from "@/components/ui/Icon";
import { getLocale } from "@/lib/i18n/getLocale";
import { getDictionary, interpolate } from "@/lib/i18n/dictionaries";

// Portage de web/utils/components.py::render_strengths_weaknesses() —
// PCT_INTERPRETATIONS déplacé dans les dictionnaires i18n (lib/i18n/
// dictionaries/{fr,en,es}.ts, clé pctInterpretations) pour être traduit.
export async function StrengthsWeaknesses({ row }: { row: Record<string, unknown> }) {
  const t = getDictionary(await getLocale());
  const pcts: [string, number][] = [];
  for (const col of Object.keys(t.pctInterpretations)) {
    const v = row[col];
    if (typeof v === "number") pcts.push([col, v]);
  }
  if (pcts.length === 0) return null;

  const sorted = [...pcts].sort((a, b) => b[1] - a[1]);
  const strengths = sorted.filter(([, v]) => v >= 75).slice(0, 3);
  const weaknesses = [...sorted].reverse().filter(([, v]) => v <= 30).slice(0, 3);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
      <div>
        <div className="text-[0.7rem] font-bold uppercase tracking-[2px] text-primary mb-2.5 flex items-center gap-1">
          <Icon name="trending_up" />
          {t.radar.strengths}
        </div>
        {strengths.length > 0 ? (
          strengths.map(([c, v]) => (
            <div key={c} className="strength-item">
              <div>{t.pctInterpretations[c as keyof typeof t.pctInterpretations][0]}</div>
              <div className="text-[0.65rem] opacity-60 mt-1">
                {interpolate(t.radar.topAtPosition, { pct: Math.max(1, 100 - Math.trunc(v)) })} ·{" "}
                {t.metrics[c as keyof typeof t.metrics] ?? c}
              </div>
            </div>
          ))
        ) : (
          <p className="text-text-muted text-sm">—</p>
        )}
      </div>
      <div>
        <div className="text-[0.7rem] font-bold uppercase tracking-[2px] text-danger mb-2.5 flex items-center gap-1">
          <Icon name="trending_down" color="#E05252" />
          {t.radar.weaknesses}
        </div>
        {weaknesses.length > 0 ? (
          weaknesses.map(([c, v]) => (
            <div key={c} className="weakness-item">
              <div>{t.pctInterpretations[c as keyof typeof t.pctInterpretations][1]}</div>
              <div className="text-[0.65rem] opacity-60 mt-1">
                {interpolate(t.radar.amongWeakest, { pct: Math.max(1, Math.trunc(v)) })} ·{" "}
                {t.metrics[c as keyof typeof t.metrics] ?? c}
              </div>
            </div>
          ))
        ) : (
          <p className="text-text-muted text-sm">—</p>
        )}
      </div>
    </div>
  );
}
