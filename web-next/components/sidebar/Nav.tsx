"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/components/i18n/I18nProvider";
import { LanguageSwitcher } from "@/components/i18n/LanguageSwitcher";
import { ThemeToggle } from "@/components/theme/ThemeToggle";

// Portage 1:1 de web/utils/sidebar.py::NAV_ITEMS — Explorer et Classement GK
// volontairement absents (retirés du menu côté Streamlit, joignables par
// URL directe uniquement) : /explorer et /classement-gk existent comme
// pages mais ne sont pas listées ici.
type NavLink = { href: string; label: string; icon: string };
type NavGroup = { section: string; collapsible: boolean; links: NavLink[] };

function NavItem({ item, pathname }: { item: NavLink; pathname: string }) {
  return (
    <Link
      href={item.href}
      className={`flex items-center gap-2.5 rounded-lg my-0.5 px-2 py-2 text-[0.9rem] font-medium transition-colors ${
        pathname === item.href
          ? "bg-overlay text-text"
          : "text-text-nav hover:bg-overlay hover:text-text"
      }`}
    >
      <span className="material-icons-outlined text-[18px] text-text-muted" aria-hidden>
        {item.icon}
      </span>
      {item.label}
    </Link>
  );
}

export function Nav() {
  const pathname = usePathname();
  const { t } = useI18n();
  // Repliés par défaut ; la section contenant la page active s'affiche
  // quand même ouverte (cf. isOpen) sans écraser ce que l'utilisateur a
  // choisi pour les autres sections.
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

  const topLink: NavLink = { href: "/", label: t.nav.dashboard, icon: "dashboard" };
  const topPepitesLink: NavLink = { href: "/championnats", label: t.nav.topPepites, icon: "emoji_events" };
  const navGroups: NavGroup[] = [
    {
      section: t.nav.fieldPlayersSection,
      collapsible: true,
      links: [
        { href: "/radar-joueur", label: t.nav.radarPlayer, icon: "radar" },
        { href: "/comparaison", label: t.nav.comparison, icon: "compare_arrows" },
        { href: "/progression", label: t.nav.progression, icon: "trending_up" },
      ],
    },
    {
      section: t.nav.goalkeepersSection,
      collapsible: true,
      links: [
        { href: "/radar-gk", label: t.nav.radarGk, icon: "radar" },
        { href: "/comparaison-gk", label: t.nav.comparisonGk, icon: "compare_arrows" },
        { href: "/progression-gk", label: t.nav.progressionGk, icon: "trending_up" },
      ],
    },
  ];

  function toggle(section: string) {
    setOpenSections((prev) => ({ ...prev, [section]: !prev[section] }));
  }

  function isOpen(group: NavGroup) {
    if (!group.collapsible) return true;
    if (group.links.some((l) => l.href === pathname)) return true;
    return !!openSections[group.section];
  }

  return (
    <nav className="px-2">
      <div className="text-center py-4">
        <div className="text-2xl mb-1">⚽</div>
        <div className="text-[1.3rem] font-extrabold text-primary tracking-wide">RadarPépites</div>
        <div className="text-[0.65rem] text-text-muted mt-0.5">
          {t.nav.tagline} · 10 {t.sidebar.footer}
        </div>
      </div>

      <div className="flex gap-2 px-1 mb-3">
        <div className="flex-1">
          <LanguageSwitcher />
        </div>
        <div className="flex-1">
          <ThemeToggle />
        </div>
      </div>

      <div className="border-t border-border mb-2" />

      <NavItem item={topLink} pathname={pathname} />
      <NavItem item={topPepitesLink} pathname={pathname} />

      {navGroups.map((group) => {
        const open = isOpen(group);
        return (
          <div key={group.section}>
            {group.collapsible ? (
              <button
                type="button"
                onClick={() => toggle(group.section)}
                aria-expanded={open}
                className="w-full flex items-center justify-between px-2 pt-3.5 pb-1.5 text-[0.65rem] font-bold uppercase tracking-[2px] text-text-muted hover:text-text-nav transition-colors"
              >
                <span>{group.section}</span>
                <span
                  className="material-icons-outlined text-[16px] transition-transform duration-200"
                  style={{ transform: open ? "rotate(0deg)" : "rotate(-90deg)" }}
                  aria-hidden
                >
                  expand_more
                </span>
              </button>
            ) : (
              <div className="text-[0.65rem] font-bold uppercase tracking-[2px] text-text-muted px-2 pt-3.5 pb-1.5">
                {group.section}
              </div>
            )}
            <div
              style={{
                maxHeight: open ? group.links.length * 44 : 0,
                overflow: "hidden",
                transition: "max-height 0.25s ease",
              }}
            >
              <div>
                {group.links.map((item) => (
                  <NavItem key={item.href} item={item} pathname={pathname} />
                ))}
              </div>
            </div>
          </div>
        );
      })}

      <div className="border-t border-border mt-3 mb-1" />
    </nav>
  );
}
