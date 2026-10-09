"use client";

import { useEffect, useState } from "react";

// Wrapper pour toutes les images hotlinkées (Sofascore via /api/img,
// flagcdn.com) : masque proprement l'image si elle échoue à charger
// (ex. Sofascore indisponible), au lieu de laisser le navigateur afficher
// l'icône "image cassée".
//
// Le <img> n'est rendu qu'après le montage client (useEffect, pas pendant
// le SSR) : si on le rendait dès le HTML serveur, le navigateur démarre son
// chargement avant même que React n'ait fini d'hydrater et d'attacher
// onError, et l'event error natif passe inaperçu pour les images proches du
// viewport (constaté en prod : logos de certaines cartes cassés, d'autres
// non, selon qu'elles aient eu le temps d'hydrater avant le chargement).
export function SafeImg({
  src,
  alt = "",
  className,
}: {
  src: string | null | undefined;
  alt?: string;
  className?: string;
}) {
  const [mounted, setMounted] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!src || failed || !mounted) return null;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} className={className} onError={() => setFailed(true)} />
  );
}
