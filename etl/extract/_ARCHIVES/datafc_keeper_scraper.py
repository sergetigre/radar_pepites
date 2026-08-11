# =============================================================
# RadarPépites — Scraping Sofascore Gardiens → Bronze
# Fichier  : etl/extract/datafc_keeper_scraper.py
# Rôle     : Récupère les stats spécifiques gardiens
#            via datafc (Sofascore) pour les 10 ligues
#            Métriques : saves, goalsPrevented + stats communes
# Pilotage : config/scraping_config.json
# Usage    : python etl/extract/datafc_keeper_scraper.py
# =============================================================

import os
import sys
import json
import time
import logging
from datetime import datetime

import pandas as pd
import datafc

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

DIR_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_BRONZE = os.path.join(DIR_ROOT, "data", "bronze")
DIR_LOGS   = os.path.join(DIR_ROOT, "logs")
CONFIG     = os.path.join(DIR_ROOT, "config", "scraping_config.json")

DELAY = 3

# ---------------------------------------------------------------------------
# IDs Sofascore + season_ids
# ---------------------------------------------------------------------------

LEAGUES = {
    "ENG": {"tournament_id": 17,  "nom": "Premier League"},
    "ESP": {"tournament_id": 8,   "nom": "La Liga"},
    "GER": {"tournament_id": 35,  "nom": "Bundesliga"},
    "ITA": {"tournament_id": 23,  "nom": "Serie A"},
    "FRA": {"tournament_id": 34,  "nom": "Ligue 1"},
    "POR": {"tournament_id": 238, "nom": "Primeira Liga"},
    "NED": {"tournament_id": 37,  "nom": "Eredivisie"},
    "BEL": {"tournament_id": 38,  "nom": "Pro League"},
    "TUR": {"tournament_id": 52,  "nom": "Super Lig"},
    "AUT": {"tournament_id": 45,  "nom": "Bundesliga Autriche"},
}

SEASON_IDS = {
    17:  {"22/23": 41886, "23/24": 52186, "24/25": 61627, "25/26": 76986},
    8:   {"22/23": 42409, "23/24": 52376, "24/25": 61643, "25/26": 77559},
    35:  {"22/23": 42268, "23/24": 52608, "24/25": 63516, "25/26": 77333},
    23:  {"22/23": 42415, "23/24": 52760, "24/25": 63515, "25/26": 76457},
    34:  {"22/23": 42273, "23/24": 52571, "24/25": 61736, "25/26": 77356},
    238: {"22/23": 42655, "23/24": 52769, "24/25": 63670, "25/26": 77806},
    37:  {"22/23": 42256, "23/24": 52554, "24/25": 61666, "25/26": 77012},
    38:  {"22/23": 42404, "23/24": 52383, "24/25": 61459, "25/26": 77040},
    52:  {"22/23": 42632, "23/24": 53190, "24/25": 63814, "25/26": 77805},
    45:  {"22/23": 42386, "23/24": 52524, "24/25": 62629, "25/26": 77382},
}

# Toutes les métriques gardiens récupérées en un seul appel
# Un seul appel = une ligne par gardien avec toutes les colonnes renseignées
KEEPER_FIELDS = [
    "saves",                       # Arrêts
    "goalsPrevented",              # Buts évités (xG contre - buts encaissés)
    "rating",                      # Note globale
    "minutesPlayed",               # Minutes jouées
    "appearances",                 # Matchs joués
    "accuratePasses",              # Passes réussies (distribution courte)
    "accurateLongBalls",           # Passes longues réussies (relances)
    "accurateLongBallsPercentage", # % passes longues réussies
    "yellowCards",                 # Cartons jaunes
    "redCards",                    # Cartons rouges
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_BRONZE, exist_ok=True)
os.makedirs(DIR_LOGS,   exist_ok=True)

log_file = os.path.join(DIR_LOGS, f"datafc_keeper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.Keeper.Sofascore")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_season_id(tournament_id: int, season: str) -> int | None:
    parts      = season.split("-")
    season_key = f"{parts[0][-2:]}/{parts[1][-2:]}"
    sid        = SEASON_IDS.get(tournament_id, {}).get(season_key)
    if sid:
        log.info(f"    season_id={sid} ({season_key})")
    else:
        log.warning(f"    season_id non trouvé pour {season_key}")
    return sid


def scrape_keeper_stats(tournament_id: int,
                        season_id: int) -> pd.DataFrame | None:
    """
    Récupère les stats gardiens via datafc en UN SEUL appel.
    fields = toutes les métriques → une ligne par gardien, toutes colonnes renseignées.
    Trié par saves (métrique principale des gardiens).
    """
    try:
        df = datafc.league_player_stats_data(
            tournament_id = tournament_id,
            season_id     = season_id,
            order         = "-saves",      # Trié par nombre d'arrêts
            fields        = KEEPER_FIELDS, # Toutes les métriques en une fois
            accumulation  = "total",
            position      = "G",           # Gardiens uniquement
            max_players   = 100,           # ~20-30 GK par ligue, 100 suffit
            rate_limit    = 2.0,
        )

        if df is not None and not df.empty:
            log.info(f"    → {len(df)} gardiens récupérés")
            log.info(f"    → Colonnes : {[c for c in df.columns if not c.startswith('_')]}")
            return df
        else:
            log.warning(f"    → Aucune donnée")
            return None

    except datafc.RateLimitError:
        log.warning(f"    Rate limit — pause 30s...")
        time.sleep(30)
        return None
    except datafc.DataNotAvailableError:
        log.warning(f"    Données non disponibles")
        return None
    except Exception as e:
        log.error(f"    Erreur : {e}")
        return None


def save_bronze(df: pd.DataFrame, league_key: str, season: str) -> str:
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(
        DIR_BRONZE,
        f"{timestamp}_{league_key}_{saison_fmt}_keeper_sofascore.csv"
    )
    df["_league_id"]  = league_key
    df["_season"]     = season
    df["_source"]     = "datafc_sofascore_keeper"
    df["_scraped_at"] = datetime.now().isoformat()
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    return filename

# ---------------------------------------------------------------------------
# Exécution principale
# ---------------------------------------------------------------------------

def load_config() -> dict:
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def run():
    config         = load_config()
    ligues_actives = [l for l in config["ligues"] if l.get("actif") is True]
    saisons        = config["saisons"]
    ligues_cibles  = [l for l in ligues_actives if l["id"] in LEAGUES]

    total    = len(ligues_cibles) * len(saisons)
    success  = 0
    failures = []
    counter  = 0

    log.info("=" * 65)
    log.info("  RadarPepites - Scraping Sofascore Gardiens -> Bronze")
    log.info("=" * 65)
    log.info(f"  Ligues  : {[l['id'] for l in ligues_cibles]}")
    log.info(f"  Saisons : {saisons}")
    log.info(f"  Stats   : {KEEPER_FIELDS}")
    log.info(f"  Filtre  : position=G (gardiens uniquement)")
    log.info(f"  Total   : {total} combinaisons ligue x saison")
    log.info("=" * 65)

    for ligue in ligues_cibles:
        league_key    = ligue["id"]
        info          = LEAGUES[league_key]
        tournament_id = info["tournament_id"]
        nom           = info["nom"]

        for season in saisons:
            counter += 1
            log.info(f"[{counter}/{total}] {nom} | {season}")

            season_id = get_season_id(tournament_id, season)
            if not season_id:
                failures.append(f"{league_key}_{season}")
                continue

            df = scrape_keeper_stats(tournament_id, season_id)

            if df is not None and not df.empty:
                path = save_bronze(df, league_key, season)
                log.info(f"  -> {len(df)} lignes -> {os.path.basename(path)}")
                success += 1
            else:
                failures.append(f"{league_key}_{season}")
                log.warning(f"  -> Aucune donnee : {league_key}_{season}")

            time.sleep(DELAY)

    log.info("=" * 65)
    log.info(f"  Termine  : {success}/{total}")
    if failures:
        log.warning(f"  Echecs   : {failures}")
    log.info("=" * 65)

if __name__ == "__main__":
    run()
