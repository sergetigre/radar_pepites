// Équivalent de st.metric() + [data-testid="metric-container"]
// (web/utils/styles.py) : libellé gris discret, valeur en gros.
export function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="kpi-container">
      <div className="text-text-muted text-sm">{label}</div>
      <div className="text-[1.65rem] font-semibold text-text mt-1 leading-tight">{value}</div>
    </div>
  );
}
