"""
web/utils/media.py — Photos joueurs, logos clubs/ligues, drapeaux pays.

Photos et logos : hotlinkés directement depuis Sofascore (pas de téléchargement/
stockage côté projet) via les identifiants déjà présents en base
(dim_joueurs.player_id_ss, dim_equipes.team_id_ss) — vérifié manuellement que
ces endpoints d'image publics fonctionnent sans authentification.

Drapeaux : Sofascore n'expose pas d'endpoint drapeau simple et fiable ; on
utilise plutôt des emoji Unicode, construits à partir d'un code ISO 3166-1
alpha-2 dérivé du code pays stocké en base (mélange de codes FIFA et ISO
alpha-3 selon les pays, d'où la table de correspondance explicite plutôt
qu'une conversion générique).
"""

import pandas as pd

SOFASCORE_IMG_BASE = "https://www.sofascore.com/api/v1"

# ligue_id (dim_ligues) -> tournament_id Sofascore (mêmes IDs que ceux utilisés
# pour le scraping, cf. etl/extract/datafc_scraper_all.py::SEASON_IDS).
LIGUE_TOURNAMENT_IDS = {
    "ENG": 17, "ESP": 8, "GER": 35, "ITA": 23, "FRA": 34,
    "POR": 238, "NED": 37, "BEL": 38, "TUR": 52, "AUT": 45,
}

# Code pays (dim_joueurs.nationalite_principale / silver.ref_pays) -> ISO
# 3166-1 alpha-2, pour construire l'emoji drapeau. Couvre les 138 codes
# distincts observés en base ; mélange de codes FIFA (ex. GER, NED, POR,
# SUI, DEN, CRO, URU, PAR, CRC, CTA, CHI) et ISO alpha-3 (ex. GRC, BIH)
# selon la source d'origine de chaque pays dans le pipeline.
COUNTRY_TO_ISO2 = {
    "AGO": "AO", "ALB": "AL", "ARE": "AE", "ARG": "AR", "ARM": "AM",
    "AUS": "AU", "AUT": "AT", "AZE": "AZ", "BDI": "BI", "BEL": "BE",
    "BEN": "BJ", "BES": "BQ", "BFA": "BF", "BGD": "BD", "BGR": "BG",
    "BIH": "BA", "BLR": "BY", "BRA": "BR", "BRB": "BB", "CAN": "CA",
    "CHI": "CL", "CIV": "CI", "CMR": "CM", "COD": "CD", "COG": "CG",
    "COL": "CO", "COM": "KM", "CPV": "CV", "CRC": "CR", "CRO": "HR",
    "CTA": "CF", "CUB": "CU", "CUW": "CW", "CYP": "CY", "CZE": "CZ",
    "DEN": "DK", "DOM": "DO", "DZA": "DZ", "ECU": "EC", "EGY": "EG",
    "ENG": "GB", "ERI": "ER", "ESP": "ES", "EST": "EE", "FIN": "FI",
    "FRA": "FR", "FRO": "FO", "GAB": "GA", "GEO": "GE", "GER": "DE",
    "GHA": "GH", "GLP": "GP", "GMB": "GM", "GNB": "GW", "GNQ": "GQ",
    "GRC": "GR", "GRD": "GD", "GUF": "GF", "GUI": "GN", "HND": "HN",
    "HTI": "HT", "HUN": "HU", "IDN": "ID", "IRL": "IE", "IRN": "IR",
    "IRQ": "IQ", "ISL": "IS", "ISR": "IL", "ITA": "IT", "JAM": "JM",
    "JOR": "JO", "JPN": "JP", "KAZ": "KZ", "KEN": "KE", "KOR": "KR",
    "KVX": "XK", "LBR": "LR", "LBY": "LY", "LTU": "LT", "LUX": "LU",
    "LVA": "LV", "MAR": "MA", "MDA": "MD", "MDG": "MG", "MEX": "MX",
    "MKD": "MK", "MLI": "ML", "MLT": "MT", "MNE": "ME", "MOZ": "MZ",
    "MRT": "MR", "MTQ": "MQ", "MYS": "MY", "NCL": "NC", "NED": "NL",
    "NER": "NE", "NGA": "NG", "NIR": "GB", "NOR": "NO", "NZL": "NZ",
    "PAN": "PA", "PAR": "PY", "PER": "PE", "PHL": "PH", "POL": "PL",
    "POR": "PT", "PRI": "PR", "PSE": "PS", "ROU": "RO", "RUS": "RU",
    "RWA": "RW", "SAU": "SA", "SCO": "GB", "SEN": "SN", "SLE": "SL",
    "SRB": "RS", "SUI": "CH", "SUR": "SR", "SVK": "SK", "SVN": "SI",
    "SWE": "SE", "SYR": "SY", "TCD": "TD", "TGO": "TG", "THA": "TH",
    "TTO": "TT", "TUN": "TN", "TUR": "TR", "TZA": "TZ", "UKR": "UA",
    "URU": "UY", "USA": "US", "UZB": "UZ", "VEN": "VE", "WAL": "GB",
    "ZAF": "ZA", "ZMB": "ZM", "ZWE": "ZW",
}

# Séquences emoji drapeau dédiées (nations britanniques constitutives, pas
# de code ISO propre) — utilisées en priorité sur COUNTRY_TO_ISO2 ci-dessus.
_SPECIAL_FLAGS = {
    "ENG": "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",  # 🏴 England
    "SCO": "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F",  # 🏴 Scotland
    "WAL": "\U0001F3F4\U000E0067\U000E0062\U000E0077\U000E006C\U000E0073\U000E007F",  # 🏴 Wales
}


def flag_emoji(country_code: str | None) -> str:
    """Emoji drapeau à partir d'un code pays base (FIFA/ISO alpha-3 mélangés).
    Retourne une chaîne vide si le code est manquant/inconnu."""
    if not country_code or pd.isna(country_code):
        return ""
    code = str(country_code).strip().upper()
    if code in _SPECIAL_FLAGS:
        return _SPECIAL_FLAGS[code]
    iso2 = COUNTRY_TO_ISO2.get(code)
    if not iso2:
        return ""
    return "".join(chr(0x1F1E6 + (ord(c) - ord("A"))) for c in iso2)


def _sofascore_image_url(kind: str, entity_id) -> str | None:
    if entity_id is None or pd.isna(entity_id):
        return None
    try:
        entity_id = int(entity_id)
    except (TypeError, ValueError):
        return None
    return f"{SOFASCORE_IMG_BASE}/{kind}/{entity_id}/image"


def player_photo_url(player_id_ss) -> str | None:
    return _sofascore_image_url("player", player_id_ss)


def team_logo_url(team_id_ss) -> str | None:
    return _sofascore_image_url("team", team_id_ss)


def ligue_logo_url(ligue_id: str | None) -> str | None:
    if not ligue_id:
        return None
    tid = LIGUE_TOURNAMENT_IDS.get(str(ligue_id).strip().upper())
    return _sofascore_image_url("unique-tournament", tid) if tid else None
