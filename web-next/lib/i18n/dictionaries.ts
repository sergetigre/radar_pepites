import fr, { type Dictionary } from "./dictionaries/fr";
import en from "./dictionaries/en";
import es from "./dictionaries/es";
import type { Locale } from "./locales";

export const dictionaries: Record<Locale, Dictionary> = { fr, en, es };
export type { Dictionary };

export function getDictionary(locale: Locale): Dictionary {
  return dictionaries[locale];
}

// Interpolation simple "{clé}" -> valeur, pour les chaînes paramétrées
// (ex. dashboard.subtitle). Pas de pluriel/formatage avancé (ICU) —
// inutile vu le volume de texte du site, juste du remplacement direct.
export function interpolate(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) => String(vars[key] ?? `{${key}}`));
}
