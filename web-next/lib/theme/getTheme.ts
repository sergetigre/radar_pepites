import { cookies } from "next/headers";
import { DEFAULT_THEME, THEME_COOKIE, isTheme, type Theme } from "./theme";

// Même principe que lib/i18n/getLocale.ts : cookie lu côté serveur pour
// que le premier rendu HTML ait déjà le bon data-theme (pas de flash du
// mauvais thème à l'hydratation).
export async function getTheme(): Promise<Theme> {
  const store = await cookies();
  const raw = store.get(THEME_COOKIE)?.value;
  return isTheme(raw) ? raw : DEFAULT_THEME;
}
