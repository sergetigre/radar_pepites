import { PCT_INTERPRETATIONS } from "@/lib/strengths-weaknesses";
import { Icon } from "@/components/ui/Icon";

// Portage 1:1 de web/utils/components.py::render_strengths_weaknesses()
export function StrengthsWeaknesses({ row }: { row: Record<string, unknown> }) {
  const pcts: [string, number][] = [];
  for (const col of Object.keys(PCT_INTERPRETATIONS)) {
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
          Points forts
        </div>
        {strengths.length > 0 ? (
          strengths.map(([c, v]) => (
            <div key={c} className="strength-item">
              <div>{PCT_INTERPRETATIONS[c][1]}</div>
              <div className="text-[0.65rem] opacity-60 mt-1">
                Top {Math.max(1, 100 - Math.trunc(v))}% à son poste · {PCT_INTERPRETATIONS[c][0]}
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
          Axes d&apos;amélioration
        </div>
        {weaknesses.length > 0 ? (
          weaknesses.map(([c, v]) => (
            <div key={c} className="weakness-item">
              <div>{PCT_INTERPRETATIONS[c][2]}</div>
              <div className="text-[0.65rem] opacity-60 mt-1">
                Parmi les {Math.max(1, Math.trunc(v))}% les plus faibles à son poste ·{" "}
                {PCT_INTERPRETATIONS[c][0]}
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
