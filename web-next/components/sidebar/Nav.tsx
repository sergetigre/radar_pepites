"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

// Portage 1:1 de web/utils/sidebar.py::NAV_ITEMS — Explorer et Classement GK
// volontairement absents (retirés du menu côté Streamlit, joignables par
// URL directe uniquement) : /explorer et /classement-gk existent comme
// pages mais ne sont pas listées ici.
type NavLink = { href: string; label: string; icon: string };
type NavGroup = { section: string; collapsible: boolean; links: NavLink[] };

const TOP_LINK: NavLink = { href: "/", label: "Tableau de bord", icon: "dashboard" };
const TOP_PEPITES_LINK: NavLink = { href: "/championnats", label: "Top pépites", icon: "emoji_events" };

const NAV_GROUPS: NavGroup[] = [
  {
    section: "Joueurs de champ",
    collapsible: true,
    links: [
      { href: "/radar-joueur", label: "Radar Joueur", icon: "radar" },
      { href: "/comparaison", label: "Comparaison", icon: "compare_arrows" },
      { href: "/progression", label: "Progression", icon: "trending_up" },
    ],
  },
  {
    section: "Gardiens",
    collapsible: true,
    links: [
      { href: "/radar-gk", label: "Radar GK", icon: "radar" },
      { href: "/comparaison-gk", label: "Comparaison GK", icon: "compare_arrows" },
      { href: "/progression-gk", label: "Progression GK", icon: "trending_up" },
    ],
  },
];

function NavItem({ item, pathname }: { item: NavLink; pathname: string }) {
  return (
    <Link
      href={item.href}
      className={`flex items-center gap-2.5 rounded-lg my-0.5 px-2 py-2 text-[0.9rem] font-medium transition-colors ${
        pathname === item.href
          ? "bg-white/[0.06] text-white"
          : "text-text-nav hover:bg-white/[0.06] hover:text-white"
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
  // Repliés par défaut ; la section contenant la page active s'affiche
  // quand même ouverte (cf. isOpen) sans écraser ce que l'utilisateur a
  // choisi pour les autres sections.
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

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
        <div className="text-[0.65rem] text-text-muted mt-0.5">Analyse U23 · 10 ligues</div>
      </div>
      <div className="border-t border-border mb-2" />

      <NavItem item={TOP_LINK} pathname={pathname} />
      <NavItem item={TOP_PEPITES_LINK} pathname={pathname} />

      {NAV_GROUPS.map((group) => {
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
