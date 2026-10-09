import { cookies } from "next/headers";
import { DEFAULT_LOCALE, LOCALE_COOKIE, isLocale, type Locale } from "./locales";

// Lecture de la langue courante côté serveur (Server Components) — pas de
// routage par URL (/fr, /en...), juste un cookie. Pas de restructuration
// des routes existantes, choix validé explicitement avec l'utilisateur.
export async function getLocale(): Promise<Locale> {
  const store = await cookies();
  const raw = store.get(LOCALE_COOKIE)?.value;
  return isLocale(raw) ? raw : DEFAULT_LOCALE;
}
