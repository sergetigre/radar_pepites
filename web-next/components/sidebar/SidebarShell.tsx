"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Icon } from "@/components/ui/Icon";

// Deux mécanismes de visibilité coexistent, indépendants l'un de l'autre :
// - Desktop (≥768px, md) : sidebar toujours dans le flux, repli/dépli via
//   `collapsed` (pousse le contenu, bouton flottant au bord — comportement
//   d'origine inchangé).
// - Mobile (<768px) : sidebar en tiroir (`position: fixed`, hors du flux),
//   masqué par défaut, ouvert via `mobileOpen` (hamburger en haut),
//   recouvre le contenu avec un fond assombri, se referme automatiquement
//   à la navigation (changement de pathname) ou au clic sur le fond.
export function SidebarShell({
  sidebar,
  children,
}: {
  sidebar: React.ReactNode;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => setMobileOpen(false), [pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <>
      <div className="md:hidden sticky top-0 z-30 flex items-center gap-3 bg-sidebar border-b border-border px-4 py-3">
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          aria-label="Ouvrir le menu"
          className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-overlay"
        >
          <Icon name="menu" size={22} color="var(--color-text-nav)" />
        </button>
        <span className="font-extrabold text-primary tracking-wide">RadarPépites</span>
      </div>

      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/60 z-40"
          onClick={() => setMobileOpen(false)}
          aria-hidden
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 md:z-auto shrink-0 bg-sidebar border-border min-h-screen overflow-hidden transition-transform md:transition-[width,border-width] duration-200 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 ${collapsed ? "md:w-0 md:border-r-0" : "w-[280px] border-r"}`}
      >
        <div className="w-[280px] h-full overflow-y-auto">{sidebar}</div>
      </aside>

      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        aria-label={collapsed ? "Afficher le menu" : "Masquer le menu"}
        aria-expanded={!collapsed}
        className="hidden md:flex fixed top-4 z-50 items-center justify-center w-7 h-7 rounded-full bg-card border border-border transition-[left] duration-200 hover:border-primary"
        style={{ left: collapsed ? 10 : 266 }}
      >
        <Icon name={collapsed ? "chevron_right" : "chevron_left"} size={18} color="var(--color-text-muted)" />
      </button>

      <main className="flex-1 min-w-0 px-4 md:px-8 py-4 md:py-6 max-w-[1400px]">{children}</main>
    </>
  );
}
