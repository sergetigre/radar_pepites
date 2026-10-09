"use client";

import { useI18n } from "@/components/i18n/I18nProvider";
import { LOCALES, LOCALE_LABELS } from "@/lib/i18n/locales";

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();
  return (
    <div className="flex gap-1" role="group" aria-label="Langue">
      {LOCALES.map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => setLocale(l)}
          aria-pressed={locale === l}
          className={`flex-1 text-[0.7rem] font-bold rounded-md py-1 transition-colors ${
            locale === l
              ? "bg-primary text-black"
              : "bg-overlay text-text-muted hover:text-text-nav"
          }`}
        >
          {LOCALE_LABELS[l]}
        </button>
      ))}
    </div>
  );
}
