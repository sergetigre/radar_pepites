# =============================================================
# RadarPépites — Scraping Sofascore → Bronze
# Fichier  : etl/extract/sofascore_scraper.py
# Rôle     : Récupère stats joueurs via API Sofascore
#            API stable : api.sofascore.com/api/v1/
#            Couvre les 10 ligues, 4 saisons
# Pilotage : config/scraping_config.json
# Usage    : python etl/extract/sofascore_scraper.py
# =============================================================

import os
import sys
import json
import time
import logging
from datetime import datetime

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

DIR_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_BRONZE = os.path.join(DIR_ROOT, "data", "bronze")
DIR_LOGS   = os.path.join(DIR_ROOT, "logs")
CONFIG     = os.path.join(DIR_ROOT, "config", "scraping_config.json")

BASE_URL = "https://api.sofascore.com/api/v1"
DELAY    = 4

# ---------------------------------------------------------------------------
# IDs Sofascore des 10 ligues (unique-tournament IDs)
# + IDs des saisons par année (season IDs Sofascore)
# ---------------------------------------------------------------------------

SOFASCORE_LEAGUES = {
    "ENG": {
        "id": 17,
        "nom": "Premier League",
        "seasons": {
            "2022-2023": 41886,
            "2023-2024": 52186,
            "2024-2025": 61627,
            "2025-2026": 63814,
        }
    },
    "ESP": {
        "id": 8,
        "nom": "La Liga",
        "seasons": {
            "2022-2023": 42409,
            "2023-2024": 52376,
            "2024-2025": 61643,
            "2025-2026": 63916,
        }
    },
    "GER": {
        "id": 35,
        "nom": "Bundesliga",
        "seasons": {
            "2022-2023": 40557,
            "2023-2024": 52608,
            "2024-2025": 63516,
            "2025-2026": 64828,
        }
    },
    "ITA": {
        "id": 23,
        "nom": "Serie A",
        "seasons": {
            "2022-2023": 42415,
            "2023-2024": 52760,
            "2024-2025": 63515,
            "2025-2026": 64827,
        }
    },
    "FRA": {
        "id": 34,
        "nom": "Ligue 1",
        "seasons": {
            "2022-2023": 40557,
            "2023-2024": 52571,
            "2024-2025": 63518,
            "2025-2026": 64829,
        }
    },
    "POR": {
        "id": 238,
        "nom": "Primeira Liga",
        "seasons": {
            "2022-2023": 42268,
            "2023-2024": 52781,
            "2024-2025": 63519,
            "2025-2026": 64830,
        }
    },
    "NED": {
        "id": 37,
        "nom": "Eredivisie",
        "seasons": {
            "2022-2023": 42273,
            "2023-2024": 52554,
            "2024-2025": 63520,
            "2025-2026": 64831,
        }
    },
    "BEL": {
        "id": 11,
        "nom": "First Division A",
        "seasons": {
            "2022-2023": 42270,
            "2023-2024": 52562,
            "2024-2025": 63521,
            "2025-2026": 64832,
        }
    },
    "TUR": {
        "id": 52,
        "nom": "Super Lig",
        "seasons": {
            "2022-2023": 42271,
            "2023-2024": 52596,
            "2024-2025": 63522,
            "2025-2026": 64833,
        }
    },
    "AUT": {
        "id": 45,
        "nom": "Bundesliga Autriche",
        "seasons": {
            "2022-2023": 42272,
            "2023-2024": 52563,
            "2024-2025": 63523,
            "2025-2026": 64834,
        }
    },
}

# Filtres de stats disponibles sur Sofascore
# Chaque appel retourne les top joueurs pour une métrique
STAT_FILTERS = [
    "rating",
    "goals",
    "assists",
    "accuratePasses",
    "keyPasses",
    "tackles",
    "interceptions",
    "dribbleSuccess",
    "minutesPlayed",
    "yellowCards",
    "redCards",
    "expectedGoals",
    "successfulLongBalls",
    "accurateCrosses",
    "shotsOnTarget",
    "bigChancesCreated",
    "clearances",
    "blockedShots",
    "aerialDuelsWon",
    "totalDuelsWon",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept":     "application/json",
    "Referer":    "https://www.sofascore.com/",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_BRONZE, exist_ok=True)
os.makedirs(DIR_LOGS,   exist_ok=True)

log_file = os.path.join(DIR_LOGS, f"sofascore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.Sofascore")

session = requests.Session()
session.headers.update(HEADERS)

# ---------------------------------------------------------------------------
# Récupération du vrai seasonId depuis l'API Sofascore
# ---------------------------------------------------------------------------

def get_real_season_id(tournament_id: int, season: str) -> int | None:
    """
    Récupère les saisons disponibles pour un tournoi et retourne
    le bon seasonId. Fallback sur l'ID configuré si non trouvé.
    """
    url = f"{BASE_URL}/unique-tournament/{tournament_id}/seasons"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None

        seasons = r.json().get("seasons", [])
        year_start = int(season.split("-")[0])
        year_end   = int(season.split("-")[1])

        for s in seasons:
            s_year = s.get("year", "")
            if (str(year_start) in str(s_year) and
                    str(year_end) in str(s_year)):
                return s.get("id")

        # Si non trouvé, retourne le premier (saison la plus récente)
        if seasons:
            return seasons[0].get("id")
        return None

    except Exception as e:
        log.error(f"    get_real_season_id : {e}")
        return None

# ---------------------------------------------------------------------------
# Récupération des stats joueurs
# ---------------------------------------------------------------------------

def get_player_stats(tournament_id: int, season_id: int,
                     stat_filter: str, page: int = 0) -> list:
    """
    Récupère les stats joueurs via l'endpoint statistics de Sofascore.
    Pagination possible (100 joueurs par page).
    URL : /unique-tournament/{id}/season/{sid}/statistics
    """
    url = (
        f"{BASE_URL}/unique-tournament/{tournament_id}"
        f"/season/{season_id}/statistics"
        f"?limit=100&order=-{stat_filter}&accumulation=total"
        f"&fields={stat_filter}&page={page}"
    )

    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            log.warning(f"      HTTP {r.status_code} : {stat_filter} p{page}")
            return []

        data    = r.json()
        results = data.get("results", [])
        rows    = []

        for item in results:
            player     = item.get("player", {})
            team       = item.get("team", {})
            statistics = item.get("statistics", {})

            row = {
                "player_id":       player.get("id"),
                "player_name":     player.get("name"),
                "player_slug":     player.get("slug"),
                "date_naissance":  player.get("dateOfBirthTimestamp"),
                "position":        player.get("position"),
                "nationalite":     player.get("country", {}).get("alpha2"),
                "team_id":         team.get("id"),
                "team_name":       team.get("name"),
                "stat_filter":     stat_filter,
                # Stats principales
                "rating":          statistics.get("rating"),
                "goals":           statistics.get("goals"),
                "assists":         statistics.get("assists"),
                "minutes_played":  statistics.get("minutesPlayed"),
                "matches_played":  statistics.get("matchesPlayed"),
                "yellow_cards":    statistics.get("yellowCards"),
                "red_cards":       statistics.get("redCards"),
                "shots_on_target": statistics.get("shotsOnTarget"),
                "key_passes":      statistics.get("keyPasses"),
                "accurate_passes": statistics.get("accuratePasses"),
                "tackles":         statistics.get("tackles"),
                "interceptions":   statistics.get("interceptions"),
                "dribble_success": statistics.get("successfulDribbles"),
                "expected_goals":  statistics.get("expectedGoals"),
                "big_chances":     statistics.get("bigChancesCreated"),
                "clearances":      statistics.get("clearances"),
                "aerial_duels":    statistics.get("aerialDuelsWon"),
            }
            rows.append(row)

        return rows

    except Exception as e:
        log.error(f"      Erreur {stat_filter} p{page} : {e}")
        return []

# ---------------------------------------------------------------------------
# Sauvegarde Bronze
# ---------------------------------------------------------------------------

def save_bronze(rows: list, league_key: str, season: str) -> str:
    df = pd.DataFrame(rows).drop_duplicates(subset=["player_id", "stat_filter"])
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(DIR_BRONZE, f"{timestamp}_{league_key}_{saison_fmt}_sofascore.csv")
    df["_league_id"]  = league_key
    df["_season"]     = season
    df["_source"]     = "sofascore"
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
    ligues_ss      = [l for l in ligues_actives if l["id"] in SOFASCORE_LEAGUES]

    total   = len(ligues_ss) * len(saisons)
    success = 0
    failures = []
    counter  = 0

    log.info("=" * 65)
    log.info("  RadarPepites - Scraping Sofascore -> Bronze")
    log.info("=" * 65)
    log.info(f"  Ligues  : {[l['id'] for l in ligues_ss]}")
    log.info(f"  Saisons : {saisons}")
    log.info(f"  Stats   : {len(STAT_FILTERS)} filtres")
    log.info(f"  Total   : {total} combinaisons ligue x saison")
    log.info("=" * 65)

    for ligue in ligues_ss:
        league_key    = ligue["id"]
        ss_info       = SOFASCORE_LEAGUES[league_key]
        tournament_id = ss_info["id"]
        nom           = ss_info["nom"]

        for season in saisons:
            counter += 1
            log.info(f"[{counter}/{total}] {nom} | {season}")

            # Récupération du seasonId réel
            season_id = get_real_season_id(tournament_id, season)

            if not season_id:
                # Fallback sur l'ID configuré
                season_id = ss_info["seasons"].get(season)

            if not season_id:
                log.warning(f"  -> seasonId introuvable")
                failures.append(f"{league_key}_{season}")
                continue

            log.info(f"  -> seasonId : {season_id}")
            time.sleep(DELAY)

            # Scraping de tous les filtres stats
            all_rows = []
            for stat_filter in STAT_FILTERS:
                rows = get_player_stats(tournament_id, season_id, stat_filter)
                log.info(f"    {stat_filter} -> {len(rows)} joueurs")
                all_rows.extend(rows)
                time.sleep(DELAY)

            if all_rows:
                path = save_bronze(all_rows, league_key, season)
                log.info(f"  -> {len(all_rows)} lignes -> {os.path.basename(path)}")
                success += 1
            else:
                failures.append(f"{league_key}_{season}")
                log.warning(f"  -> Aucune donnee : {league_key}_{season}")

            log.info(f"  -> Pause {DELAY}s...")
            time.sleep(DELAY)

    log.info("=" * 65)
    log.info(f"  Termine  : {success}/{total} fichiers generes")
    if failures:
        log.warning(f"  Echecs   : {failures}")
    log.info(f"  Bronze   : {DIR_BRONZE}")
    log.info("=" * 65)

if __name__ == "__main__":
    run()
