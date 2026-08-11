# =============================================================
# RadarPépites — Infos joueurs et équipes → Bronze
# Fichier  : etl/extract/datafc_players_info.py
# Rôle     : Récupère les données biographiques des joueurs
#            et les infos équipes via datafc (Sofascore)
# Chaîne   : standings → squad → player
# Usage    : python etl/extract/datafc_players_info.py
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

DELAY = 2

# ---------------------------------------------------------------------------
# IDs Sofascore + season_ids hardcodés
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

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

os.makedirs(DIR_BRONZE, exist_ok=True)
os.makedirs(DIR_LOGS,   exist_ok=True)

log_file = os.path.join(DIR_LOGS, f"players_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
log = logging.getLogger("RadarPepites.PlayersInfo")

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


def save_bronze(df: pd.DataFrame, league_key: str, season: str, data_type: str) -> str:
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_fmt = season.replace("-", "_")
    filename   = os.path.join(
        DIR_BRONZE,
        f"{timestamp}_{league_key}_{saison_fmt}_{data_type}.csv"
    )
    df["_league_id"]  = league_key
    df["_season"]     = season
    df["_source"]     = "datafc_sofascore"
    df["_scraped_at"] = datetime.now().isoformat()
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    return filename

# ---------------------------------------------------------------------------
# Pipeline par ligue × saison
# ---------------------------------------------------------------------------

def run_league_season(league_key: str, tournament_id: int,
                      season_id: int, season: str) -> dict:
    """
    Exécute la chaîne standings → squad → player pour une ligue/saison.
    Retourne un dict avec les DataFrames obtenus.
    """
    results = {}

    # ── Étape 1 : Standings (classement équipes) ──────────────────────────
    log.info(f"    [1/3] Standings...")
    try:
        df_standings = datafc.standings_data(
            tournament_id = tournament_id,
            season_id     = season_id,
            rate_limit    = 2.0,
        )
        if df_standings is not None and not df_standings.empty:
            log.info(f"    → {len(df_standings)} équipes")
            results["standings"] = df_standings
            path = save_bronze(df_standings, league_key, season, "standings")
            log.info(f"    → {os.path.basename(path)}")
        else:
            log.warning(f"    → Standings vide")
            return results
    except Exception as e:
        log.error(f"    → Standings erreur : {e}")
        return results

    time.sleep(DELAY)

    # ── Étape 2 : Squad (liste joueurs par équipe) ────────────────────────
    log.info(f"    [2/3] Squad (roster joueurs)...")
    try:
        df_squad = datafc.squad_data(
            standings_df  = df_standings,
            rate_limit    = 2.0,
        )
        if df_squad is not None and not df_squad.empty:
            log.info(f"    → {len(df_squad)} joueurs dans les squads")
            results["squad"] = df_squad
            path = save_bronze(df_squad, league_key, season, "squad")
            log.info(f"    → {os.path.basename(path)}")
        else:
            log.warning(f"    → Squad vide")
            return results
    except Exception as e:
        log.error(f"    → Squad erreur : {e}")
        return results

    time.sleep(DELAY)

    # ── Étape 3 : Player info (bio, nationalité, DOB...) ─────────────────
    log.info(f"    [3/3] Player data (infos biographiques)...")
    try:
        df_players = datafc.player_data(
            squad_df   = df_squad,
            rate_limit = 2.0,
        )
        if df_players is not None and not df_players.empty:
            log.info(f"    → {len(df_players)} joueurs avec infos bio")
            results["players"] = df_players
            path = save_bronze(df_players, league_key, season, "players_info")
            log.info(f"    → {os.path.basename(path)}")
        else:
            log.warning(f"    → Player data vide")
    except Exception as e:
        log.error(f"    → Player data erreur : {e}")

    return results

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
    log.info("  RadarPepites - Infos Joueurs & Equipes -> Bronze")
    log.info("=" * 65)
    log.info(f"  Ligues  : {[l['id'] for l in ligues_cibles]}")
    log.info(f"  Saisons : {saisons}")
    log.info(f"  Total   : {total} combinaisons ligue x saison")
    log.info(f"  Fichiers: 3 par combinaison (standings, squad, players_info)")
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

            results = run_league_season(league_key, tournament_id, season_id, season)

            if "players" in results:
                success += 1
                # Affiche un aperçu des colonnes disponibles
                cols = list(results["players"].columns)
                log.info(f"  -> Colonnes players_info : {cols[:10]}...")
            else:
                failures.append(f"{league_key}_{season}")
                log.warning(f"  -> Echec : {league_key}_{season}")

            time.sleep(DELAY)

    log.info("=" * 65)
    log.info(f"  Termine  : {success}/{total} combinaisons completes")
    if failures:
        log.warning(f"  Echecs   : {failures}")
    log.info(f"  Bronze   : {DIR_BRONZE}")
    log.info("=" * 65)

if __name__ == "__main__":
    run()
