"""
etl/extract/datafc_scraper_all.py
RadarPépites — Scraping Sofascore via datafc (10 ligues)

2 appels par ligue × saison :
  1. Joueurs de champ (position != G) → *_sofascore_players.csv
  2. Gardiens (position = G)          → *_sofascore_keepers.csv

Sorties : data/bronze/YYYYMMDD_HHMMSS_{league_id}_{saison}_sofascore_{type}.csv
Logs    : logs/datafc_all_YYYYMMDD_HHMMSS.log
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import datafc
import pandas as pd

# ── Chemins absolus ────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parents[2]
CONFIG     = ROOT / "config" / "scraping_config.json"
BRONZE_DIR = ROOT / "data" / "bronze"
LOGS_DIR   = ROOT / "logs"

BRONZE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ── IDs Sofascore ──────────────────────────────────────────────────────────────
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

# ── Métriques ──────────────────────────────────────────────────────────────────
FIELD_PLAYER_METRICS = [
    "rating", "goals", "assists", "expectedGoals", "expectedAssists",
    "shotsOnTarget", "totalShots", "bigChancesCreated", "bigChancesMissed",
    "accuratePasses", "accuratePassesPercentage", "keyPasses",
    "accurateLongBalls", "accurateLongBallsPercentage",
    "successfulDribbles", "successfulDribblesPercentage",
    "tackles", "interceptions", "clearances", "possessionLost",
    "minutesPlayed", "appearances", "yellowCards", "redCards",
]

KEEPER_METRICS = [
    "saves", "goalsPrevented", "rating", "minutesPlayed", "appearances",
    "accuratePasses", "accurateLongBalls", "accurateLongBallsPercentage",
    "yellowCards", "redCards",
]

REQUEST_DELAY_SEC = 3.0
RATE_LIMIT        = 2.0
RETRY_WAIT_SEC    = 30.0


# ── Logging ────────────────────────────────────────────────────────────────────
def setup_logger() -> logging.Logger:
    run_ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"datafc_all_{run_ts}.log"

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("datafc_all")
    logger.info(f"Log : {log_file}")
    return logger


# ── Config ─────────────────────────────────────────────────────────────────────
def load_config() -> tuple[list[str], list[str]]:
    """Retourne (saisons, league_ids actifs présents dans LEAGUES).
    Accepte ligues en dict {'ENG': {...}} ou en liste [{'id': 'ENG', ...}].
    """
    print(f"  Config chargée depuis : {CONFIG}")
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)

    saisons = cfg["saisons"]
    ligues_raw = cfg["ligues"]

    # Format dict  : {"ENG": {"nom": ..., "actif": true}, ...}
    if isinstance(ligues_raw, dict):
        actives = [
            lid for lid, meta in ligues_raw.items()
            if meta.get("actif") and lid in LEAGUES
        ]
    # Format liste : [{"id": "ENG", "nom": ..., "actif": true}, ...]
    elif isinstance(ligues_raw, list):
        actives = [
            entry.get("id", entry.get("code", ""))
            for entry in ligues_raw
            if entry.get("actif") and entry.get("id", entry.get("code", "")) in LEAGUES
        ]
    else:
        raise ValueError(f"Format 'ligues' non reconnu dans {CONFIG} : {type(ligues_raw)}")

    return saisons, actives


# ── Utilitaires ────────────────────────────────────────────────────────────────
def saison_to_sofascore_key(saison: str) -> str:
    """'2023-2024' → '23/24'."""
    parts = saison.split("-")
    return f"{parts[0][2:]}/{parts[1][2:]}"


def add_metadata(df: pd.DataFrame, league_id: str,
                 saison: str, source_tag: str) -> pd.DataFrame:
    df = df.copy()
    df["_league_id"]  = league_id
    df["_season"]     = saison
    df["_source"]     = "datafc_sofascore"
    df["_scraped_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return df


def build_output_path(league_id: str, saison: str, file_tag: str) -> Path:
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_slug = saison.replace("-", "")
    fname       = f"{ts}_{league_id}_{saison_slug}_{file_tag}.csv"
    return BRONZE_DIR / fname


def call_with_retry(fn, logger: logging.Logger, label: str):
    """Appelle fn(). Sur RateLimitError : attend 30 s et réessaie une fois."""
    try:
        return fn()
    except datafc.RateLimitError:
        logger.warning(f"  RateLimitError — pause {RETRY_WAIT_SEC}s puis retry ({label})")
        time.sleep(RETRY_WAIT_SEC)
        try:
            return fn()
        except Exception as e:
            logger.error(f"  Retry échoué ({label}) : {type(e).__name__}: {e}")
            return None
    except datafc.DataNotAvailableError as e:
        logger.warning(f"  DataNotAvailable ({label}) : {e}")
        return None
    except Exception as e:
        logger.error(f"  Erreur inattendue ({label}) : {type(e).__name__}: {e}")
        return None


# ── Scraping d'un bloc ligue × saison ─────────────────────────────────────────
def scrape_one(league_id: str, saison: str,
               logger: logging.Logger) -> tuple[bool, bool]:
    """
    Effectue les 2 appels (joueurs + gardiens).
    Retourne (ok_players, ok_keepers).
    """
    meta         = LEAGUES[league_id]
    tid          = meta["tournament_id"]
    season_key   = saison_to_sofascore_key(saison)
    season_id    = SEASON_IDS.get(tid, {}).get(season_key)

    if season_id is None:
        logger.warning(
            f"  Season ID introuvable — {league_id} | {saison} ({season_key})"
        )
        return False, False

    ok_players = ok_keepers = False

    # ── Appel 1 : joueurs de champ ──────────────────────────────────────────
    logger.info(f"  → Joueurs de champ (tournament={tid}, season={season_id})")

    def fetch_players():
        return datafc.league_player_stats_data(
            tournament_id=tid,
            season_id=season_id,
            order="-rating",
            fields=FIELD_PLAYER_METRICS,
            accumulation="total",
            max_players=500,
            rate_limit=RATE_LIMIT,
        )

    df_players = call_with_retry(fetch_players, logger, f"{league_id}|{saison}|players")

    if df_players is not None and not df_players.empty:
        stat_cols = [c for c in df_players.columns if not c.startswith("_")]
        logger.info(
            f"    {len(df_players)} joueurs | "
            f"{len(stat_cols)} colonnes : {stat_cols[:8]}{'...' if len(stat_cols) > 8 else ''}"
        )
        df_players = add_metadata(df_players, league_id, saison, "sofascore_players")
        out = build_output_path(league_id, saison, "sofascore_players")
        df_players.to_csv(out, index=False, encoding="utf-8-sig")
        logger.info(f"    ✓ {out.name}")
        ok_players = True
    else:
        logger.warning(f"    Données joueurs vides — {league_id} | {saison}")

    time.sleep(REQUEST_DELAY_SEC)

    # ── Appel 2 : gardiens ──────────────────────────────────────────────────
    logger.info(f"  → Gardiens (tournament={tid}, season={season_id})")

    def fetch_keepers():
        return datafc.league_player_stats_data(
            tournament_id=tid,
            season_id=season_id,
            order="-saves",
            fields=KEEPER_METRICS,
            accumulation="total",
            position="G",
            max_players=100,
            rate_limit=RATE_LIMIT,
        )

    df_keepers = call_with_retry(fetch_keepers, logger, f"{league_id}|{saison}|keepers")

    if df_keepers is not None and not df_keepers.empty:
        stat_cols = [c for c in df_keepers.columns if not c.startswith("_")]
        logger.info(
            f"    {len(df_keepers)} gardiens | "
            f"{len(stat_cols)} colonnes : {stat_cols}"
        )
        df_keepers = add_metadata(df_keepers, league_id, saison, "sofascore_keepers")
        out = build_output_path(league_id, saison, "sofascore_keepers")
        df_keepers.to_csv(out, index=False, encoding="utf-8-sig")
        logger.info(f"    ✓ {out.name}")
        ok_keepers = True
    else:
        logger.warning(f"    Données gardiens vides — {league_id} | {saison}")

    return ok_players, ok_keepers


# ── Point d'entrée ─────────────────────────────────────────────────────────────
def main():
    logger           = setup_logger()
    saisons, league_ids = load_config()

    tasks   = [(lid, sai) for lid in league_ids for sai in saisons]
    total   = len(tasks)
    files_generated = 0
    failures        = []

    logger.info("=" * 65)
    logger.info("  datafc — Scraping All (joueurs + gardiens)")
    logger.info(f"  Ligues  : {league_ids}")
    logger.info(f"  Saisons : {saisons}")
    logger.info(f"  Total   : {total} blocs (× 2 appels = {total * 2} requêtes)")
    logger.info("=" * 65)

    for i, (league_id, saison) in enumerate(tasks, 1):
        logger.info(
            f"[{i:>{len(str(total))}}/{total}] "
            f"{LEAGUES[league_id]['nom']} ({league_id}) | {saison}"
        )
        ok_p, ok_k = scrape_one(league_id, saison, logger)

        if ok_p:
            files_generated += 1
        else:
            failures.append(f"{league_id} | {saison} | players")

        if ok_k:
            files_generated += 1
        else:
            failures.append(f"{league_id} | {saison} | keepers")

        if i < total:
            time.sleep(REQUEST_DELAY_SEC)

    successes = total * 2 - len(failures)
    logger.info("=" * 65)
    logger.info(f"  BILAN : {successes}/{total * 2} appels réussis")
    logger.info(f"  Fichiers générés : {files_generated}")
    if failures:
        logger.warning(f"  Échecs ({len(failures)}) :")
        for f in failures:
            logger.warning(f"    - {f}")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
