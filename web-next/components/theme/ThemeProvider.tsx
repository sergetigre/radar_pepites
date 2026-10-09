"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { THEME_COOKIE, type Theme } from "@/lib/theme/theme";

type ThemeContextValue = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

// Contrairement à I18nProvider, pas de router.refresh() ici : le thème est
// purement visuel (CSS via l'attribut data-theme sur <html>, cf.
// globals.css), aucun contenu Server Component ne change avec lui.
export function ThemeProvider({
  theme,
  children,
}: {
  theme: Theme;
  children: React.ReactNode;
}) {
  const [current, setCurrent] = useState<Theme>(theme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", current);
  }, [current]);

  function setTheme(t: Theme) {
    document.cookie = `${THEME_COOKIE}=${t}; path=/; max-age=31536000`;
    setCurrent(t);
  }

  function toggleTheme() {
    setTheme(current === "dark" ? "light" : "dark");
  }

  return (
    <ThemeContext.Provider value={{ theme: current, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
