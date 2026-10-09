export const THEMES = ["dark", "light"] as const;
export type Theme = (typeof THEMES)[number];
export const DEFAULT_THEME: Theme = "dark";
export const THEME_COOKIE = "NEXT_THEME";

export function isTheme(v: string | undefined | null): v is Theme {
  return !!v && (THEMES as readonly string[]).includes(v);
}
