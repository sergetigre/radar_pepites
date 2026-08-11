"""
etl/extract/fbref_scraper_all.py
RadarPépites — Scraping FBref via soccerdata (Big 5 uniquement)

Stat types collectés :
  standard, shooting, playing_time, misc  → tous joueurs
  keeper, keeper_adv                      → gardiens uniquement

Sorties : data/bronze/YYYYMMDD_HHMMSS_{league_id}_{saison}_{stat_type}.csv
Logs    : logs/fbref_all_YYYYMMDD_HHMMSS.log
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import soccerdata as sd

# ── Chemins absolus ────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parents[2]
CONFIG     = ROOT / "config" / "scraping_config.json"
BRONZE_DIR = ROOT / "data" / "bronze"
LOGS_DIR   = ROOT / "logs"

BRONZE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ── Constantes ─────────────────────────────────────────────────────────────────
BIG5 = {"ENG", "ESP", "GER", "ITA", "FRA"}

# Mapping league_id → code soccerdata
FBREF_LEAGUE_CODES = {
    "ENG": "ENG-Premier League",
    "ESP": "ESP-La Liga",
    "GER": "GER-Bundesliga",
    "ITA": "ITA-Serie A",
    "FRA": "FRA-Ligue 1",
}

STAT_TYPES = [
    "standard",
    "shooting",
    "playing_time",
    "misc",
    "keeper",
    "keeper_adv",
]

REQUEST_DELAY_SEC = 4.0


# ── Logging ────────────────────────────────────────────────────────────────────
def setup_logger() -> logging.Logger:
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"fbref_all_{run_ts}.log"

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("fbref_all")
    logger.info(f"Log : {log_file}")
    return logger


# ── Config ─────────────────────────────────────────────────────────────────────
def load_config() -> tuple[list[str], list[str]]:
    """Retourne (saisons, league_ids actifs dans Big5).
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
            if meta.get("actif") and lid in BIG5
        ]
    # Format liste : [{"id": "ENG", "nom": ..., "actif": true}, ...]
    elif isinstance(ligues_raw, list):
        actives = [
            entry.get("id", entry.get("code", ""))
            for entry in ligues_raw
            if entry.get("actif") and entry.get("id", entry.get("code", "")) in BIG5
        ]
    else:
        raise ValueError(f"Format 'ligues' non reconnu dans {CONFIG} : {type(ligues_raw)}")

    return saisons, actives


# ── Utilitaires ────────────────────────────────────────────────────────────────
def saison_to_fbref(saison: str) -> int:
    """'2023-2024' → 2023  (soccerdata attend l'année de début)."""
    return int(saison.split("-")[0])


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplatit un MultiIndex de colonnes en '{niveau1}_{niveau2}'."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join(str(c).strip() for c in col if c).strip("_")
            for col in df.columns
        ]
    return df


def add_metadata(df: pd.DataFrame, league_id: str, saison: str,
                 stat_type: str) -> pd.DataFrame:
    df = df.copy()
    df["_league_id"]  = league_id
    df["_season"]     = saison
    df["_stat_type"]  = stat_type
    df["_source"]     = "fbref_soccerdata"
    df["_scraped_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return df


def build_output_path(league_id: str, saison: str, stat_type: str) -> Path:
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    saison_slug = saison.replace("-", "")
    fname  = f"{ts}_{league_id}_{saison_slug}_{stat_type}.csv"
    return BRONZE_DIR / fname


# ── Scraping d'un bloc ─────────────────────────────────────────────────────────
def scrape_one(league_id: str, saison: str, stat_type: str,
               logger: logging.Logger) -> bool:
    league_code = FBREF_LEAGUE_CODES[league_id]
    year        = saison_to_fbref(saison)

    try:
        fbref = sd.FBref(leagues=league_code, seasons=year)
        df    = fbref.read_player_season_stats(stat_type=stat_type)

        if df is None or df.empty:
            logger.warning(f"  Données vides — {league_id} | {saison} | {stat_type}")
            return False

        df = flatten_columns(df)
        df = df.reset_index()
        df = add_metadata(df, league_id, saison, stat_type)

        out = build_output_path(league_id, saison, stat_type)
        df.to_csv(out, index=False, encoding="utf-8-sig")
        logger.info(f"  ✓ {out.name}  ({len(df)} lignes, {len(df.columns)} colonnes)")
        return True

    except Exception as e:
        logger.error(f"  ✗ {league_id} | {saison} | {stat_type} → {type(e).__name__}: {e}")
        return False


# ── Point d'entrée ─────────────────────────────────────────────────────────────
def main():
    logger  = setup_logger()
    saisons, league_ids = load_config()

    tasks = [
        (lid, sai, st)
        for lid in league_ids
        for sai in saisons
        for st  in STAT_TYPES
    ]
    total   = len(tasks)
    success = 0
    failures = []

    logger.info("=" * 65)
    logger.info(f"  FBref — Scraping All Stats")
    logger.info(f"  Ligues  : {league_ids}")
    logger.info(f"  Saisons : {saisons}")
    logger.info(f"  Types   : {STAT_TYPES}")
    logger.info(f"  Total   : {total} blocs")
    logger.info("=" * 65)

    for i, (league_id, saison, stat_type) in enumerate(tasks, 1):
        logger.info(
            f"[{i:>{len(str(total))}}/{total}] "
            f"{league_id} | {saison} | {stat_type}"
        )
        ok = scrape_one(league_id, saison, stat_type, logger)
        if ok:
            success += 1
        else:
            failures.append(f"{league_id} | {saison} | {stat_type}")

        if i < total:
            time.sleep(REQUEST_DELAY_SEC)

    logger.info("=" * 65)
    logger.info(f"  BILAN : {success}/{total} succès")
    if failures:
        logger.warning(f"  Échecs ({len(failures)}) :")
        for f in failures:
            logger.warning(f"    - {f}")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
