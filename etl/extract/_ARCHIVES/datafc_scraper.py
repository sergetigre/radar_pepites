# =============================================================
# RadarPépites — Scraping datafc (Sofascore) → Bronze
# Fichier  : etl/extract/datafc_scraper.py
# Usage    : python etl/extract/datafc_scraper.py
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
# IDs Sofascore validés (unique-tournament IDs)
# Vérifiés depuis sofascore.com/tournament/football/...
# ---------------------------------------------------------------------------

LEAGUES = {
    "ENG": {"tournament_id": 17,  "nom": "Premier League"},
    "ESP": {"tournament_id": 8,   "nom": "La Liga"},
    "GER": {"tournament_id": 35,  "nom": "Bundesliga"},
    "ITA": {"tournament_id": 23,  "nom": "Serie A"},
    "FRA": {"tournament_id": 34,  "nom": "Ligue 1"},
    "POR": {"tournament_id": 238, "nom": "Primeira Liga"},
    "NED": {"tournament_id": 37,  "nom": "Eredivisie"},
    "BEL": {"tournament_id": 38,  "nom": "First Division A"},
    "TUR": {"tournament_id": 52,  "nom": "Super Lig"},
    "AUT": {"tournament_id": 45,  "nom": "Bundesliga Autriche"},
}

# Season IDs hardcodés depuis les logs précédents — 100% fiables
# Format : ligue_id → saison_key → season_id
SEASON_IDS = {
    17:  {"23/24": 52186, "24/25": 61627, "25/26": 76986, "22/23": 41886},
    8:   {"23/24": 52376, "24/25": 61643, "25/26": 77559, "22/23": 42409},
    35:  {"23/24": 52608, "24/25": 63516, "25/26": 77333, "22/23": 42268},
    23:  {"23/24": 52760, "24/25": 63515, "25/26": 76457, "22/23": 42415},
    34:  {"23/24": 52571, "24/25": 61736, "25/26": 77356, "22/23": 42273},
    238: {"23/24": 52769, "24/25": 63670, "25/26": 77806, "22/23": 42655},
    37:  {"23/24": 52554, "24/25": 61666, "25/26": 77012, "22/23": 42256},
    38:  {"22/23": 42404, "23/24": 52383, "24/25": 61459, "25/26": 77040},
    52:  {"23/24": 53190, "24/25": 63814, "25/26": 77805, "22/23": 42632},
    45:  {"23/24": 52524, "24/25": 62629, "25/26": 77382, "22/23": 42386},
}

# Métriques valides confirmées par l'API datafc
METRICS = [
    "rating", "goals", "assists", "expectedGoals", "expectedAssists",
    "shotsOnTarget", "totalShots", "bigChancesCreated", "bigChancesMissed",
    "accuratePasses", "accuratePassesPercentage", "keyPasses",
    "accurateLongBalls", "accurateLongBallsPercentage",
    "successfulDribbles", "successfulDribblesPercentage",
    "tackles", "interceptions", "clearances", "possessionLost",
    "minutesPlayed", "appearances", "yellowCards", "redCards",
    "saves", "goalsPrevented",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_BRONZE, exist_ok=True)
os.makedirs(DIR_LOGS,   exist_ok=True)

log_file = os.path.join(DIR_LOGS, f"datafc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.datafc")

# ---------------------------------------------------------------------------
# Récupération du season_id
# ---------------------------------------------------------------------------

def get_season_id(tournament_id: int, season: str) -> int | None:
    """
    Récupère le season_id Sofascore.
    Priorité : table hardcodée → puis API dynamique
    """
    # Conversion : "2023-2024" → "23/24"
    parts = season.split("-")
    season_key = f"{parts[0][-2:]}/{parts[1][-2:]}"

    # 1. Lookup dans la table hardcodée
    hardcoded = SEASON_IDS.get(tournament_id, {})
    sid = hardcoded.get(season_key)
    if sid:
        log.info(f"    {season} → {season_key} → season_id={sid} (hardcoded)")
        return sid

    # 2. Fallback dynamique via API
    try:
        df_seasons = datafc.seasons_data(tournament_id=tournament_id)
        if df_seasons is None or df_seasons.empty:
            log.warning(f"    Aucune saison retournée pour tournament_id={tournament_id}")
            return None

        for _, row in df_seasons.iterrows():
            s_year = str(row.get("season_year", ""))
            if s_year == season_key:
                sid = int(row.get("season_id") or 0)
                if sid:
                    log.info(f"    {season} → {season_key} → season_id={sid} (API)")
                    return sid

        log.warning(f"    {season} ({season_key}) non trouvée pour tournament_id={tournament_id}")
        return None

    except Exception as e:
        log.error(f"    get_season_id erreur : {e}")
        return None

# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def scrape_league(tournament_id: int, season_id: int) -> pd.DataFrame | None:
    """
    Récupère toutes les stats joueurs en UN SEUL appel.
    fields = toutes les métriques → une ligne par joueur, toutes colonnes renseignées.
    Trié par rating (métrique globale la plus représentative).
    """
    try:
        df = datafc.league_player_stats_data(
            tournament_id = tournament_id,
            season_id     = season_id,
            order         = "-rating",   # Trié par note globale
            fields        = METRICS,     # Toutes les métriques en une fois
            accumulation  = "total",
            max_players   = 500,         # Augmenté pour couvrir tous les joueurs
            rate_limit    = 2.0,
        )

        if df is not None and not df.empty:
            log.info(f"    → {len(df)} joueurs")
            log.info(f"    → Colonnes stats : {[c for c in df.columns if c in METRICS]}")
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

# ---------------------------------------------------------------------------
# Sauvegarde Bronze
# ---------------------------------------------------------------------------

def save_bronze(df: pd.DataFrame, league_key: str, season: str) -> str:
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(DIR_BRONZE, f"{timestamp}_{league_key}_{saison_fmt}_datafc.csv")
    df["_league_id"]  = league_key
    df["_season"]     = season
    df["_source"]     = "datafc_sofascore"
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
    log.info("  RadarPepites - Scraping datafc -> Bronze")
    log.info("=" * 65)
    log.info(f"  Ligues  : {[l['id'] for l in ligues_cibles]}")
    log.info(f"  Saisons : {saisons}")
    log.info(f"  Metrics : {len(METRICS)}")
    log.info(f"  Total   : {total} combinaisons")
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
                log.warning(f"  -> season_id introuvable, on passe")
                failures.append(f"{league_key}_{season}")
                continue

            df = scrape_league(tournament_id, season_id)

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
