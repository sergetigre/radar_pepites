# =============================================================
# RadarPépites - Extraction fbref → Bronze
# Fichier  : etl/extract/fbref_scraper.py
# Rôle     : Scrape les stats joueurs fbref pour les 10 ligues
#            et sauvegarde les CSV bruts horodatés dans data/bronze/
# Usage    : python etl/extract/fbref_scraper.py
#            python etl/extract/fbref_scraper.py --league ENG
#            python etl/extract/fbref_scraper.py --stat shooting
# =============================================================

import os
import sys
import time
import argparse
import logging
from datetime import datetime

import pandas as pd
import soccerdata as sd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEASON = "2024-2025"

LEAGUES = {
    "ENG": "ENG-Premier League",
    "ESP": "ESP-La Liga",
    "GER": "GER-Bundesliga",
    "ITA": "ITA-Serie A",
    "FRA": "FRA-Ligue 1",
    "POR": "POR-Primeira Liga",
    "NED": "NED-Eredivisie",
    "BEL": "BEL-First Division A",
    "TUR": "TUR-Super Lig",
    "AUT": "AUT-Bundesliga",
}

# Types de stats disponibles sur fbref via soccerdata
STAT_TYPES = [
    "standard",      # Buts, passes décisives, minutes, xG, xAG
    "shooting",      # Tirs, tirs cadrés, distance moyenne
    "passing",       # Passes tentées/réussies, passes progressives
    "passing_types", # Types de passes (longues, courtes, centres...)
    "goal_shot_creation",  # GCA, SCA
    "defense",       # Tacles, interceptions, pressing
    "possession",    # Dribbles, courses progressives, réceptions
    "misc",          # Cartons, fautes, duels aériens
]

DIR_BRONZE = "data/bronze"
DIR_LOGS   = "logs"
DELAY      = 4  # secondes entre chaque requête (respecter rate-limit fbref)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_LOGS, exist_ok=True)
os.makedirs(DIR_BRONZE, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"{DIR_LOGS}/scraping_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)
log = logging.getLogger("RadarPépites")

# ---------------------------------------------------------------------------
# Fonctions
# ---------------------------------------------------------------------------

def scrape_stat(league_key: str, league_name: str, stat_type: str) -> pd.DataFrame | None:
    """
    Scrape un type de stats pour une ligue depuis fbref.
    Retourne un DataFrame ou None en cas d'erreur.
    """
    log.info(f"Scraping {league_key} | {stat_type}...")
    try:
        fbref = sd.FBref(leagues=league_name, seasons=SEASON)
        df = fbref.read_player_season_stats(stat_type=stat_type)

        # Aplatir le MultiIndex de colonnes si présent
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join(filter(None, col)).strip() for col in df.columns]

        # Ajouter les métadonnées de traçabilité
        df["_league_id"]    = league_key
        df["_league_name"]  = league_name
        df["_stat_type"]    = stat_type
        df["_season"]       = SEASON
        df["_scraped_at"]   = datetime.now().isoformat()

        log.info(f"  → {len(df)} lignes récupérées")
        return df

    except Exception as e:
        log.error(f"  → ERREUR {league_key} | {stat_type} : {e}")
        return None


def save_bronze(df: pd.DataFrame, league_key: str, stat_type: str) -> str:
    """
    Sauvegarde le DataFrame brut en CSV horodaté dans data/bronze/.
    Convention de nommage : YYYYMMDD_HHMMSS_ENG_standard.csv
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"{DIR_BRONZE}/{timestamp}_{league_key}_{stat_type}.csv"
    df.to_csv(filename, index=True, encoding="utf-8-sig")
    log.info(f"  → Sauvegardé : {filename}")
    return filename


def run(leagues_filter: list = None, stats_filter: list = None):
    """
    Lance le scraping complet ou partiel.
    leagues_filter : liste de league_key à scraper (ex: ['ENG', 'FRA'])
    stats_filter   : liste de stat_type à scraper (ex: ['standard', 'shooting'])
    """
    leagues_to_scrape = {
        k: v for k, v in LEAGUES.items()
        if leagues_filter is None or k in leagues_filter
    }
    stats_to_scrape = [
        s for s in STAT_TYPES
        if stats_filter is None or s in stats_filter
    ]

    total    = len(leagues_to_scrape) * len(stats_to_scrape)
    success  = 0
    failures = []

    log.info("=" * 60)
    log.info(f"RadarPépites — Scraping Bronze")
    log.info(f"Ligues  : {list(leagues_to_scrape.keys())}")
    log.info(f"Stats   : {stats_to_scrape}")
    log.info(f"Saison  : {SEASON}")
    log.info(f"Total   : {total} fichiers à générer")
    log.info("=" * 60)

    for league_key, league_name in leagues_to_scrape.items():
        for stat_type in stats_to_scrape:
            df = scrape_stat(league_key, league_name, stat_type)

            if df is not None and not df.empty:
                save_bronze(df, league_key, stat_type)
                success += 1
            else:
                failures.append(f"{league_key}_{stat_type}")

            # Pause entre chaque requête — NE PAS SUPPRIMER
            # fbref bloque les IPs qui envoient trop de requêtes trop vite
            log.info(f"  → Pause {DELAY}s (rate-limit fbref)...")
            time.sleep(DELAY)

    # Bilan
    log.info("=" * 60)
    log.info(f"Scraping terminé : {success}/{total} fichiers générés")
    if failures:
        log.warning(f"Échecs : {failures}")
    log.info(f"Fichiers dans : {DIR_BRONZE}/")
    log.info("=" * 60)


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="RadarPépites — Scraping fbref vers Bronze"
    )
    parser.add_argument(
        "--league",
        nargs="+",
        choices=list(LEAGUES.keys()),
        help="Ligues à scraper (ex: --league ENG FRA). Par défaut : toutes.",
    )
    parser.add_argument(
        "--stat",
        nargs="+",
        choices=STAT_TYPES,
        help="Types de stats à scraper (ex: --stat standard shooting). Par défaut : tous.",
    )
    args = parser.parse_args()

    run(
        leagues_filter=args.league,
        stats_filter=args.stat,
    )