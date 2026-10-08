// Portage 1:1 de web/utils/components.py::render_terrain_svg()
const POSITIONS: Record<string, [number, number]> = {
  GK: [50, 122],
  CB: [50, 100], LB: [18, 100], RB: [82, 100],
  DM: [50, 80],
  CM: [50, 60], LM: [18, 60], RM: [82, 60],
  AM: [50, 40],
  LW: [15, 25], RW: [85, 25],
  FW: [50, 15],
  MF: [50, 60], DF: [50, 100],
};

export function TerrainSvg({ poste, width = 160 }: { poste: string; width?: number }) {
  const [px, py] = POSITIONS[poste] ?? [50, 50];
  const h = Math.round(width * 1.4);
  const r = Math.round(width * 0.04);

  return (
    <svg width={width} height={h} viewBox="0 0 100 140" xmlns="http://www.w3.org/2000/svg">
      <rect width="100" height="140" rx="4" fill="#0D1A12" />
      <rect x="5" y="5" width="90" height="130" rx="2" fill="none" stroke="#2DAD7E" strokeWidth="1.2" opacity="0.6" />
      <line x1="5" y1="70" x2="95" y2="70" stroke="#2DAD7E" strokeWidth="0.8" opacity="0.4" />
      <circle cx="50" cy="70" r="12" fill="none" stroke="#2DAD7E" strokeWidth="0.8" opacity="0.4" />
      <rect x="25" y="115" width="50" height="20" fill="none" stroke="#2DAD7E" strokeWidth="0.8" opacity="0.4" />
      <rect x="25" y="5" width="50" height="20" fill="none" stroke="#2DAD7E" strokeWidth="0.8" opacity="0.4" />
      <circle cx={px} cy={py} r={r + 1} fill="#2DAD7E" opacity="0.25" />
      <circle cx={px} cy={py} r={r} fill="#2DAD7E" />
    </svg>
  );
}
