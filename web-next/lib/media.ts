// Portage 1:1 de web/utils/media.py — photos joueurs, logos clubs/ligues,
// drapeaux pays. Hotlinks Sofascore directs (pas de stockage cote projet).
// Fichier serveur ET client (aucune dependance a lib/db.ts).

const SOFASCORE_IMG_BASE = "https://www.sofascore.com/api/v1";

// ligue_id (dim_ligues) -> tournament_id Sofascore.
export const LIGUE_TOURNAMENT_IDS: Record<string, number> = {
  ENG: 17,
  ESP: 8,
  GER: 35,
  ITA: 23,
  FRA: 34,
  POR: 238,
  NED: 37,
  BEL: 38,
  TUR: 52,
  AUT: 45
};

// Code pays (dim_joueurs.nationalite_principale) -> ISO 3166-1 alpha-2,
// pour construire l'emoji drapeau. Melange de codes FIFA et ISO alpha-3
// selon la source d'origine de chaque pays dans le pipeline.
const COUNTRY_TO_ISO2: Record<string, string> = {
  AGO: "AO", ALB: "AL", ARE: "AE", ARG: "AR", ARM: "AM",
  AUS: "AU", AUT: "AT", AZE: "AZ", BDI: "BI", BEL: "BE",
  BEN: "BJ", BES: "BQ", BFA: "BF", BGD: "BD", BGR: "BG",
  BIH: "BA", BLR: "BY", BRA: "BR", BRB: "BB", CAN: "CA",
  CHI: "CL", CIV: "CI", CMR: "CM", COD: "CD", COG: "CG",
  COL: "CO", COM: "KM", CPV: "CV", CRC: "CR", CRO: "HR",
  CTA: "CF", CUB: "CU", CUW: "CW", CYP: "CY", CZE: "CZ",
  DEN: "DK", DOM: "DO", DZA: "DZ", ECU: "EC", EGY: "EG",
  ENG: "GB", ERI: "ER", ESP: "ES", EST: "EE", FIN: "FI",
  FRA: "FR", FRO: "FO", GAB: "GA", GEO: "GE", GER: "DE",
  GHA: "GH", GLP: "GP", GMB: "GM", GNB: "GW", GNQ: "GQ",
  GRC: "GR", GRD: "GD", GUF: "GF", GUI: "GN", HND: "HN",
  HTI: "HT", HUN: "HU", IDN: "ID", IRL: "IE", IRN: "IR",
  IRQ: "IQ", ISL: "IS", ISR: "IL", ITA: "IT", JAM: "JM",
  JOR: "JO", JPN: "JP", KAZ: "KZ", KEN: "KE", KOR: "KR",
  KVX: "XK", LBR: "LR", LBY: "LY", LTU: "LT", LUX: "LU",
  LVA: "LV", MAR: "MA", MDA: "MD", MDG: "MG", MEX: "MX",
  MKD: "MK", MLI: "ML", MLT: "MT", MNE: "ME", MOZ: "MZ",
  MRT: "MR", MTQ: "MQ", MYS: "MY", NCL: "NC", NED: "NL",
  NER: "NE", NGA: "NG", NIR: "GB", NOR: "NO", NZL: "NZ",
  PAN: "PA", PAR: "PY", PER: "PE", PHL: "PH", POL: "PL",
  POR: "PT", PRI: "PR", PSE: "PS", ROU: "RO", RUS: "RU",
  RWA: "RW", SAU: "SA", SCO: "GB", SEN: "SN", SLE: "SL",
  SRB: "RS", SUI: "CH", SUR: "SR", SVK: "SK", SVN: "SI",
  SWE: "SE", SYR: "SY", TCD: "TD", TGO: "TG", THA: "TH",
  TTO: "TT", TUN: "TN", TUR: "TR", TZA: "TZ", UKR: "UA",
  URU: "UY", USA: "US", UZB: "UZ", VEN: "VE", WAL: "GB",
  ZAF: "ZA", ZMB: "ZM", ZWE: "ZW",
};

// Codes de subdivision dédiés (nations britanniques constitutives, pas de
// code ISO propre) - utilisés en priorité sur COUNTRY_TO_ISO2 ci-dessus.
// Supportés tels quels par flagcdn.com (voir flagImageUrl).
const SPECIAL_ISO: Record<string, string> = {
  ENG: "gb-eng",
  SCO: "gb-sct",
  WAL: "gb-wls",
};

// Remplace l'ancien rendu en emoji Unicode (🇪🇸) : Windows/Segoe UI Emoji
// n'affiche pas les drapeaux de pays (rendu en petit encadré à 2 lettres),
// contrairement à macOS/iOS/Android — vérifié sur la machine de dev. On
// utilise donc des images SVG hotlinkées (flagcdn.com, gratuit, pas de clé),
// fiables sur toutes les plateformes.
export function flagImageUrl(countryCode: string | null | undefined): string | null {
  if (!countryCode) return null;
  const code = countryCode.trim().toUpperCase();
  const iso = SPECIAL_ISO[code] ?? COUNTRY_TO_ISO2[code]?.toLowerCase();
  return iso ? `https://flagcdn.com/${iso}.svg` : null;
}

function sofascoreImageUrl(kind: string, entityId: number | null | undefined): string | null {
  if (entityId == null) return null;
  return `${SOFASCORE_IMG_BASE}/${kind}/${entityId}/image`;
}

export function playerPhotoUrl(playerIdSs: number | null | undefined): string | null {
  return sofascoreImageUrl("player", playerIdSs);
}

export function teamLogoUrl(teamIdSs: number | null | undefined): string | null {
  return sofascoreImageUrl("team", teamIdSs);
}

export function ligueLogoUrl(ligueId: string | null | undefined): string | null {
  if (!ligueId) return null;
  const tid = LIGUE_TOURNAMENT_IDS[ligueId.trim().toUpperCase()];
  return tid ? sofascoreImageUrl("unique-tournament", tid) : null;
}
