// Portage 1:1 de web/utils/components.py::pct_bar_color() / render_pct_bars()
function pctBarColor(value: number): string {
  if (value < 33) return "#E05252";
  if (value < 66) return "#E0B452";
  return "#2DAD7E";
}

export function PctBars({
  metrics,
  title,
}: {
  metrics: Record<string, number | null | undefined>;
  title?: string;
}) {
  const entries = Object.entries(metrics).filter(([, v]) => v != null) as [string, number][];
  if (entries.length === 0) return null;

  return (
    <div>
      {title && (
        <div className="text-[0.7rem] font-bold uppercase tracking-[2px] text-text-muted mt-4 mb-2.5">
          {title}
        </div>
      )}
      {entries.map(([label, value]) => {
        const val = Math.round(value * 10) / 10;
        const color = pctBarColor(val);
        return (
          <div key={label} className="pct-bar-container">
            <div className="pct-bar-label">
              <span>{label}</span>
              <span>{val.toFixed(0)}</span>
            </div>
            <div className="pct-bar-track">
              <div className="pct-bar-fill" style={{ width: `${val}%`, background: color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
