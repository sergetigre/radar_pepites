"use client";

import { createContext, useCallback, useContext, useState } from "react";
import { useRouter } from "next/navigation";
import { dictionaries, type Dictionary, interpolate } from "@/lib/i18n/dictionaries";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n/locales";

type I18nContextValue = {
  locale: Locale;
  t: Dictionary;
  setLocale: (locale: Locale) => void;
  tf: (template: string, vars: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

// Pas de routage par URL (/fr, /en...) — juste un cookie + router.refresh()
// pour que les Server Components (pages async qui lisent getLocale() côté
// serveur) se re-rendent dans la nouvelle langue sans recharger toute la
// page. Les Client Components (Nav, Filters...) consomment ce contexte
// directement via useI18n(), mise à jour instantanée sans attendre le
// aller-retour serveur.
export function I18nProvider({
  locale,
  children,
}: {
  locale: Locale;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [current, setCurrent] = useState<Locale>(locale);

  const setLocale = useCallback(
    (l: Locale) => {
      document.cookie = `${LOCALE_COOKIE}=${l}; path=/; max-age=31536000`;
      setCurrent(l);
      router.refresh();
    },
    [router]
  );

  const value: I18nContextValue = {
    locale: current,
    t: dictionaries[current],
    setLocale,
    tf: (template, vars) => interpolate(template, vars),
  };

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
