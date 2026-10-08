// Palette dédiée par championnat — remplace couleur_hex (dim_ligues), dont
// les vraies couleurs de marque se ressemblent trop pour de la dataviz
// (plusieurs rouges quasi identiques, Pro League en noir invisible sur fond
// sombre, Ligue 1 en blanc pur). 10 teintes nettement distinctes (une par
// famille de teinte : rouge/orange/ambre/citron vert/émeraude/sarcelle/
// cyan/bleu/violet/rose), toutes lumineuses pour bien ressortir sur
// l'arrière-plan sombre du site. Utilisée partout où une couleur de
// championnat est affichée (cartes joueurs, header, graphiques).
export const LIGUE_COLORS: Record<string, string> = {
  ENG: "#F87171", // rouge
  ESP: "#FB923C", // orange
  GER: "#FBBF24", // ambre
  ITA: "#A3E635", // citron vert
  FRA: "#34D399", // émeraude
  POR: "#2DD4BF", // sarcelle
  NED: "#22D3EE", // cyan
  BEL: "#60A5FA", // bleu
  TUR: "#A78BFA", // violet
  AUT: "#F472B6", // rose
};

const DEFAULT_COLOR = "#2DAD7E";

export function ligueColor(ligueId: string | null | undefined): string {
  if (!ligueId) return DEFAULT_COLOR;
  return LIGUE_COLORS[ligueId.trim().toUpperCase()] ?? DEFAULT_COLOR;
}
