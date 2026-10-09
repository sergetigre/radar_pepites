"use client";

import { useTheme } from "@/components/theme/ThemeProvider";
import { useI18n } from "@/components/i18n/I18nProvider";
import { Icon } from "@/components/ui/Icon";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const { t } = useI18n();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-pressed={isDark}
      className="w-full flex items-center justify-center gap-1.5 text-[0.7rem] font-semibold rounded-md py-1.5 bg-overlay text-text-nav hover:text-text transition-colors"
    >
      <Icon name={isDark ? "dark_mode" : "light_mode"} size={14} color="currentColor" />
      {isDark ? t.theme.dark : t.theme.light}
    </button>
  );
}
